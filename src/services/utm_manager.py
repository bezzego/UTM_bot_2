import json
import os
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class UTMManager:
    def __init__(self, data_file: str = "data/utm_data.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        self.ensure_data_file_exists()
        self.load_data()
        self.normalize_data()

    def ensure_data_file_exists(self):
        """Создает директорию и файл данных, если он не существует или пуст."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            
            write_defaults = False
            if not os.path.exists(self.data_file):
                write_defaults = True
            else:
                # Файл существует, проверим, не пустой ли он
                try:
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Проверяем, есть ли данные в ключевых категориях
                        if not data.get("sources") and not data.get("mediums"):
                            write_defaults = True
                except (json.JSONDecodeError, FileNotFoundError):
                    # Файл поврежден, пуст или не найден
                    write_defaults = True

            if write_defaults:
                initial_data = {
                    "sources": [
                        ["VK", "vk"],
                        ["Telegram", "telegram"],
                        ["Yandex", "yandex"],
                        ["Google", "google"],
                        ["2GIS", "2gis"]
                    ],
                    "sources_other": [
                        ["Партнер", "partner"],
                        ["Блогер", "blogger"],
                        ["Сайт", "site"]
                    ],
                    "mediums": [
                        ["CPC", "cpc"],
                        ["Social", "social"],
                        ["Email", "email"],
                        ["Post", "post"],
                        ["Story", "story"]
                    ],
                    "campaigns": {
                        "spb": [
                            ["Спектакли", "spectacle"],
                            ["Концерты", "concert"],
                            ["Выставки", "exhibition"]
                        ],
                        "msk": [
                            ["Театры", "theatre_msk"],
                            ["Стендап", "standup_msk"]
                        ],
                        "regions": [
                            ["Афиша ЕКБ", "afisha_ekb"],
                            ["Афиша НСК", "afisha_nsk"]
                        ],
                        "foreign": [
                            ["Dubai Events", "dubai_events"]
                        ]
                    }
                }
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error in ensure_data_file_exists: {e}")

    def load_data(self):
        """Загружает данные из JSON файла"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.data = {
                "sources": [],
                "sources_other": [],
                "mediums": [],
                "campaigns": {"spb": [], "msk": [], "regions": [], "foreign": []}
            }

    def normalize_data(self) -> None:
        """Приводит структуру данных к ожидаемому формату"""
        data = self.data if isinstance(self.data, dict) else {}

        sources = data.get("sources")
        if not isinstance(sources, list):
            data["sources"] = []

        sources_other = data.get("sources_other")
        if not isinstance(sources_other, list):
            data["sources_other"] = []

        mediums = data.get("mediums")
        if isinstance(mediums, dict):
            merged: list = []
            for key in ("general", "items", "publications", "mailings", "stories", "channels"):
                items = mediums.get(key)
                if isinstance(items, list):
                    merged.extend(items)
            data["mediums"] = merged
        elif not isinstance(mediums, list):
            data["mediums"] = []

        campaigns = data.get("campaigns")
        if not isinstance(campaigns, dict):
            campaigns = {}
        for key in ("spb", "msk", "regions", "foreign"):
            if not isinstance(campaigns.get(key), list):
                campaigns[key] = []
        data["campaigns"] = campaigns

        self.data = data

    def save_data(self):
        """Сохраняет данные в JSON файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False

    def get_all_categories(self) -> Dict:
        """Возвращает все категории для инлайн-клавиатуры"""
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
        """Возвращает данные для конкретной категории"""
        category_map = {
            "source": ("sources", None),
            "source_other": ("sources_other", None),
            "medium": ("mediums", None),
            "campaign_spb": ("campaigns", "spb"),
            "campaign_msk": ("campaigns", "msk"),
            "campaign_regions": ("campaigns", "regions"),
            "campaign_foreign": ("campaigns", "foreign")
        }
        
        if category_key in category_map:
            main_key, sub_key = category_map[category_key]
            if sub_key:
                return self.data.get(main_key, {}).get(sub_key, [])
            else:
                return self.data.get(main_key, [])
        return []

    def add_item(self, category_key: str, name: str, value: str) -> bool:
        """Добавляет новый элемент в категорию"""
        try:
            category_map = {
                "source": ("sources", None),
                "source_other": ("sources_other", None),
                "medium": ("mediums", None),
                "campaign_spb": ("campaigns", "spb"),
                "campaign_msk": ("campaigns", "msk"),
                "campaign_regions": ("campaigns", "regions"),
                "campaign_foreign": ("campaigns", "foreign")
            }
            
            if category_key not in category_map:
                return False
            
            main_key, sub_key = category_map[category_key]
            item = [name, value]
            
            if sub_key:
                # Проверяем на дубликаты
                existing_items = self.data[main_key][sub_key]
                if any(existing_item[1] == value for existing_item in existing_items):
                    return False
                self.data[main_key][sub_key].append(item)
            else:
                # Проверяем на дубликаты
                if any(existing_item[1] == value for existing_item in self.data[main_key]):
                    return False
                self.data[main_key].append(item)
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return False

    def delete_item(self, category_key: str, value: str) -> bool:
        """Удаляет элемент из категории"""
        try:
            category_map = {
                "source": ("sources", None),
                "source_other": ("sources_other", None),
                "medium": ("mediums", None),
                "campaign_spb": ("campaigns", "spb"),
                "campaign_msk": ("campaigns", "msk"),
                "campaign_regions": ("campaigns", "regions"),
                "campaign_foreign": ("campaigns", "foreign")
            }
            
            if category_key not in category_map:
                return False
            
            main_key, sub_key = category_map[category_key]
            
            if sub_key:
                self.data[main_key][sub_key] = [
                    item for item in self.data[main_key][sub_key] 
                    if item[1] != value
                ]
            else:
                self.data[main_key] = [
                    item for item in self.data[main_key] 
                    if item[1] != value
                ]
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Error deleting item: {e}")
            return False

# Глобальный экземпляр менеджера
utm_manager = UTMManager()
