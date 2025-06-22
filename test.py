import hunspell

class TextCorrector: 
        def __init__(self, dic_path_ru, aff_path_ru, dic_path_en, aff_path_en, words):
                self.hunspell_ru = hunspell.HunSpell(dic_path_ru, aff_path_ru)
                self.hunspell_en = hunspell.HunSpell(dic_path_en, aff_path_en)
                self.add_new_word(words=words)

        def add_new_word(self, words):
            for i in words:
                self.hunspell_ru.add(i)

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


with open('ru.txt', 'r', encoding='utf-8') as f:
        custom_vocab = [line.strip().lower() for line in f]

tx = TextCorrector('./pn/ru_RU.dic', './pn/ru_RU.aff', './pn/en_US.dic', './pn/en_US.aff', custom_vocab)

print(tx.correct_vocub('Текст: ОТЧЕТ ДИЗАЙНЕРЫ 2024 Allocations Св логотипы Фирменный он for YouTube Баннера 2025 ТИР Спектр PCT Спектр Page 2 Uni site Контент Universe 20 Вепу pack Авто Visalia 2 ГО Партнера ат s а u 0 тэта ш iuD Isaac TAU aid н 86 о 9 I 8 i 51 Rid Pitta 22570 219 Zit ш ImD z 8550 w о IVIED Tritium 3 э з a 790 зги Shane ТИР Спектр Drafts Design Protat урв 8 Page Lille Assets 1 EIEIE 100 Pages Variables Page Page 2 Amylase черновик Е x рап t Layers Grasp 15410 Mask group Group 15419 стр Спектр freephone TBIOUch_774471 image 55 Union Rectangle 2571 Rectangle 2570 Rectangle 2572 Grasp 15384 Mask group Group 15418 стр Спектр image 55 U п ian Rectangle 2571 Rectangle 2570 Rectangle 2572 63/03 62/03 для попущения социальной паши обеспечения СТР двинь заказа или оперативная доставка да дворик При необходимости поможем оформить документы Самовывоз выставочного зала Grasp 15409 Frame 9828 Frame 9827 Nectar 19 Grasp 15408 Frame 9828 пи та 0 4 Frame 9827 299 C Солнечно РУС Ll 1818 58 11 06 2025 Поиск'))