import easyocr
import cv2
import numpy as np
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    Doc
)
from loguru import logger
from PIL import Image
import re
import os
from difflib import get_close_matches
from config import TEMP_DIR 
import hashlib 
from pyaspeller import YandexSpeller
import hunspell

class ImageProcessor:
    
    def __init__(self):
        with open('ru.txt', 'r', encoding='utf-8') as f:
            self.custom_vocab = [line.strip().lower() for line in f]

        self.reader = easyocr.Reader(
            lang_list=['ru', 'en'],
            gpu=True
            )
        
        
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.syntax_parser = NewsSyntaxParser(self.emb)
        self.ner_tagger = NewsNERTagger(self.emb)

        self.temp_dir = TEMP_DIR
        self.allowlist = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_,.?!:;/()@_&%+–—"\''
        self.textCorrector = self.TextCorrector('./pn/ru_RU.dic', './pn/ru_RU.aff', './pn/en_US.dic', './pn/en_US.aff')
        
    def data_in_image(self, image_path: str) -> dict:
        """Обнаружение и извлечение текстовых данных из изображения с помощью OCR."""
        image = cv2.imread(image_path)
        results = self.reader.readtext(image, paragraph=True)
        return results


    def extract_text(self, results: list) -> str:
        """Извлекает и объединяет текст из результатов OCR."""
        text_only = [detection[1] for detection in results]
        full_text = ' '.join(text_only)
        return full_text


    def selected_text_in_box(self, results: list, image_path: str) -> None:
        """Рисует рамки вокруг текста и сохраняет изображение."""
        image = cv2.imread(image_path)
        
        for detection in results:
            bbox = [[int(x), int(y)] for [x, y] in detection[0]]
            top_left = tuple(bbox[0])
            bottom_right = tuple(bbox[2])
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

        base_name = os.path.basename(image_path)
        output_path = os.path.join(self.temp_dir, f'selected_{base_name}')
        
        if not cv2.imwrite(output_path, image):
            raise ValueError("Не удалось сохранить изображение")
        

    def process_text(self, text: str) -> str:
        try:
            doc = Doc(text)
            doc.segment(self.segmenter)
            doc.tag_morph(self.morph_tagger)
            doc.parse_syntax(self.syntax_parser)
            doc.tag_ner(self.ner_tagger)

            for span in doc.spans:
                span.normalize(self.morph_vocab)

            return " ".join([
                token.text for token in doc.tokens
                if not token.pos in {'PUNCT', 'SYMB'}
            ])
        except Exception as e:
            logger.error(f"Ошибка при обработке текста: {e}")
            return text
        
    def morphological_analysis(self, text):
        """Проводит морфологический анализ"""
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.parse_syntax(self.syntax_parser)
        doc.tag_ner(self.ner_tagger)
        
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
        
        objects = "Объекты: "
        subjects = "Субъекты: "
        date = "Даты:"
        name = "Имена:"
        
        for span in doc.spans:
            if span.type == 'PER':  
                name += f'{span.text}, '
            elif span.type == 'LOC': 
                objects += f'{span.text}, '
            elif span.type == 'ORG': 
                subjects += f'{span.text}, '
            elif span.type == 'DATE':
                date += f'{span.text}, '
        
        for token in doc.tokens:
            if token.rel == 'nsubj':
                subjects += f'{token.text}, '
            elif token.rel in ('obj', 'obl'):  
                objects += f'{token.text}, '
        
        results = f"\nМорфологический анализ: {objects}; {subjects}; {name}; {date}."
        
        return results

    def clean_ocr_text(self, text: str) -> str:
        text = re.sub(r'(\w)-\s*(\w)', r'\1\2', text)
        text = re.sub(r'[^\w\s.,!?;:@/()\-–—]', '', text)
        mistakes = {
            r'\bсгг\b': 'сеть',
            r'\b[З3]адание\b': 'задание',
            r'\bв0\b': 'во'
        }

        text = re.sub(r'\.\s*\.\s*\.', '...', text) 
        text = re.sub(r'[•·∙·•]', '', text)
        text = re.sub(r'\s*\.\s*', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        for pattern, fix in mistakes.items():
            text = re.sub(pattern, fix, text, flags=re.IGNORECASE)
        return text.strip()

    def calculate_image_hash(self, image_path: str) -> str:
        """Вычисляет хеш изображения для определения дубликатов"""
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"Не удалось прочитать изображение: {image_path}")
                
            img = cv2.resize(img, (8, 8))
            avg = img.mean()
            hash_bits = img > avg
            hash_str = ''.join(['1' if bit else '0' for bit in hash_bits.flatten()])
            hash_hex = hex(int(hash_str, 2))[2:].zfill(16)
            
            return hash_hex
            
        except Exception as e:
            logger.error(f"Ошибка при вычислении хеша изображения {image_path}: {e}")
            return None
            
    def is_duplicate(self, image_path: str, image_hash: str) -> bool:
        """Проверяет, является ли изображение дубликатом"""
        try:
            current_hash = self.calculate_image_hash(image_path)
            if not current_hash:
                return False
            return current_hash == image_hash
            
        except Exception as e:
            logger.error(f"Ошибка при проверке дубликата {image_path}: {e}")
            return False

    def process_image(self, image_path: str) -> str:
        """Обрабатывает изображение и возвращает распознанный текст"""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Файл не найден: {image_path}")
            file_size = os.path.getsize(image_path)
            image_hash = self.calculate_image_hash(image_path)
            if not image_hash:
                raise ValueError("Не удалось вычислить хеш изображения")

            
            data = self.data_in_image(image_path)
            text = self.extract_text(data)

            self.selected_text_in_box(data, image_path)
            raw_text = self.clean_ocr_text(text)
            
            corrected_text_tesseract = self.textCorrector.correct_text(raw_text)
            processed_text_tesseract = self.process_text(corrected_text_tesseract)
            morh_text = self.morphological_analysis(processed_text_tesseract)

            processed_text_tesseract += morh_text

            return processed_text_tesseract
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения {image_path}: {e}")
            return None

    def cleanup(self):
        """Очищает временные файлы"""
        
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при очистке временных файлов: {e}")


    class TextCorrector: 
            def __init__(self, dic_path_ru, aff_path_ru, dic_path_en, aff_path_en):
                self.hunspell_ru = hunspell.HunSpell(dic_path_ru, aff_path_ru)
                self.hunspell_en = hunspell.HunSpell(dic_path_en, aff_path_en)

            def correct_vocub(self, text: str) -> str:
                words = text.split()
                corrected = []

                for word in words:
                    if self.is_russian(word):
                        if self.hunspell_ru.spell(word):
                            corrected.append(word)
                        else:
                            suggestions = self.hunspell_ru.suggest(word)
                            corrected.append(suggestions[0] if suggestions else word)
                    else:
                        if self.hunspell_en.spell(word):
                            corrected.append(word)
                        else:
                            suggestions = self.hunspell_en.suggest(word)
                            corrected.append(suggestions[0] if suggestions else word)

                return ' '.join(corrected)


            def is_russian(self, word: str) -> bool:
                return any('а' <= char <= 'я' or 'А' <= char <= 'Я' for char in word)



    """class TextCorrector:
            def __init__(self):
                
                self.speller_ru = YandexSpeller(lang='ru')
                self.speller_en = YandexSpeller(lang='en')
            
            def correct_text(self, text: str) -> str:
                
                # Обрабатываем русские слова
                ru_corrections = self.speller_ru.spell(text)
                for error in ru_corrections:
                    if error['s']:  # Если есть варианты исправления
                        text = text.replace(error['word'], error['s'][0])
                
                # Обрабатываем английские слова
                en_corrections = self.speller_en.spell(text)
                for error in en_corrections:
                    if error['s']:
                        text = text.replace(error['word'], error['s'][0])
                
                return text
            
            def get_corrections(self, text: str) -> list:
                
                corrections = []
                # Проверяем русские ошибки
                corrections.extend(self.speller_ru.spell(text))
                # Проверяем английские ошибки
                corrections.extend(self.speller_en.spell(text))
                
                return corrections"""
