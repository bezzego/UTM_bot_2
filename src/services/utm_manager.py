import json
import os
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class UTMManager:
    def __init__(self, data_file: str = "data/utm_data.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        self.data: Dict = {}
        self._ensure_data_file_and_load()

    def _ensure_data_file_and_load(self):
        """Гарантирует наличие файла с данными, создает его при необходимости и загружает данные."""
        created_now = False
        if not os.path.exists(self.data_file):
            self._create_default_data_file()
            created_now = True
        
        # Если файл не был только что создан, загружаем и проверяем его
        if not created_now:
            self.load_data()
            # Если данные неполные (например, пустой json), перезаписываем
            if not self.data.get("sources") or not self.data.get("mediums"):
                self._create_default_data_file()
        
        # В любом случае, в конце загружаем актуальные данные в память
        self.load_data()
        self.normalize_data()

    def _create_default_data_file(self):
        """Создает директорию и файл данных с метками по умолчанию."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            initial_data = {
                "sources": [
                    ["VK", "vk"], ["Telegram", "telegram"], ["Yandex", "yandex"], ["Google", "google"], ["2GIS", "2gis"]
                ],
                "sources_other": [
                    ["Партнер", "partner"], ["Блогер", "blogger"], ["Сайт", "site"]
                ],
                "mediums": [
                    ["CPC", "cpc"], ["Social", "social"], ["Email", "email"], ["Post", "post"], ["Story", "story"]
                ],
                "campaigns": {
                    "spb": [["Спектакли", "spectacle"], ["Концерты", "concert"], ["Выставки", "exhibition"]],
                    "msk": [["Театры", "theatre_msk"], ["Стендап", "standup_msk"]],
                    "regions": [["Афиша ЕКБ", "afisha_ekb"], ["Афиша НСК", "afisha_nsk"]],
                    "foreign": [["Dubai Events", "dubai_events"]]
                }
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error creating default data file: {e}")

    def load_data(self):
        """Загружает данные из JSON файла или создает пустую структуру."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}

    def normalize_data(self) -> None:
        """Гарантирует, что все ключи и списки существуют в self.data."""
        self.data.setdefault("sources", [])
        self.data.setdefault("sources_other", [])
        self.data.setdefault("mediums", [])
        campaigns = self.data.setdefault("campaigns", {})
        if not isinstance(campaigns, dict):
            self.data["campaigns"] = {}
        self.data["campaigns"].setdefault("spb", [])
        self.data["campaigns"].setdefault("msk", [])
        self.data["campaigns"].setdefault("regions", [])
        self.data["campaigns"].setdefault("foreign", [])

    def save_data(self) -> bool:
        """Сохраняет текущие данные в JSON файл."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False

    def get_all_categories(self) -> Dict[str, Tuple[str, str]]:
        return {
            "utm_source": ("📊 Источники трафика (utm_source)", "source"),
            "utm_source_other": ("🧩 Источники: Другое (utm_source)", "source_other"),
            "utm_medium": ("📎 Типы трафика (utm_medium)", "medium"),
            "utm_campaign_spb": ("📍 СПБ кампании", "campaign_spb"),
            "utm_campaign_msk": ("🏙 МСК кампании", "campaign_msk"),
            "utm_campaign_regions": ("🌍 Регионы кампании", "campaign_regions"),
            "utm_campaign_foreign": ("🌐 Зарубежье кампании", "campaign_foreign")
        }

    def get_category_data(self, category_key: str) -> List[Tuple[str, str]]:
        category_map = self.get_category_data_map()
        if category_key not in category_map:
            return []
        main_key, sub_key = category_map[category_key]
        if sub_key:
            return self.data.get(main_key, {}).get(sub_key, [])
        else:
            return self.data.get(main_key, [])

    def add_item(self, category_key: str, name: str, value: str) -> bool:
        category_map = self.get_category_data_map()
        if category_key not in category_map:
            return False
        main_key, sub_key = category_map[category_key]
        target_list = self.data[main_key][sub_key] if sub_key else self.data[main_key]
        if any(item[1] == value for item in target_list):
            return False
        target_list.append([name, value])
        return self.save_data()

    def delete_item(self, category_key: str, value: str) -> bool:
        category_map = self.get_category_data_map()
        if category_key not in category_map:
            return False
        main_key, sub_key = category_map[category_key]
        if sub_key:
            target_list = self.data[main_key][sub_key]
            original_len = len(target_list)
            self.data[main_key][sub_key] = [item for item in target_list if item[1] != value]
            if len(self.data[main_key][sub_key]) == original_len:
                return False
        else:
            target_list = self.data[main_key]
            original_len = len(target_list)
            self.data[main_key] = [item for item in target_list if item[1] != value]
            if len(self.data[main_key]) == original_len:
                return False
        return self.save_data()

    def get_category_data_map(self) -> Dict[str, Tuple[str, str | None]]:
        return {
            "source": ("sources", None), "source_other": ("sources_other", None),
            "medium": ("mediums", None), "campaign_spb": ("campaigns", "spb"),
            "campaign_msk": ("campaigns", "msk"), "campaign_regions": ("campaigns", "regions"),
            "campaign_foreign": ("campaigns", "foreign")
        }

# Примечание: глобальный экземпляр больше не создается здесь.
# Он будет создаваться по требованию в обработчиках.
