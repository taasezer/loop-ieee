"""
LOOP Lojistik Platformu - Uluslararasılaştırma ve Yerelleştirme
Çoklu dil, para birimi ve bölgesel ayarlar desteği
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from loguru import logger
import gettext
import locale
from babel import Locale
from babel.dates import format_date, format_time, format_datetime
from babel.numbers import format_currency, format_decimal, format_percent

from core.config import settings


class LanguageCode(Enum):
    """Desteklenen diller"""
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    ARABIC = "ar"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"


class CurrencyCode(Enum):
    """Desteklenen para birimleri"""
    TURKISH_LIRA = "TRY"
    US_DOLLAR = "USD"
    EURO = "EUR"
    BRITISH_POUND = "GBP"
    SWISS_FRANC = "CHF"
    RUSSIAN_RUBLE = "RUB"
    CHINESE_YUAN = "CNY"
    JAPANESE_YEN = "JPY"
    SAUDI_RIYAL = "SAR"


@dataclass
class RegionalSettings:
    """Bölgesel ayarlar"""
    language: LanguageCode
    currency: CurrencyCode
    timezone: str
    date_format: str
    time_format: str
    number_format: str
    measurement_system: str  # metric, imperial
    address_format: str
    phone_format: str


@dataclass
class Address:
    """Uluslararası adres formatı"""
    street: str
    city: str
    postal_code: str
    country: str
    state_province: Optional[str] = None
    district: Optional[str] = None
    building_number: Optional[str] = None
    apartment: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    
    def format_for_country(self, country_code: str) -> str:
        """Ülkeye göre adres formatla"""
        formats = {
            'TR': f"{self.street} {self.city} {self.postal_code}",
            'US': f"{self.street}, {self.city}, {self.state_province} {self.postal_code}",
            'DE': f"{self.street}\n{self.postal_code} {self.city}",
            'JP': f"〒{self.postal_code}\n{self.state_province}{self.city}{self.street}"
        }
        
        return formats.get(country_code, f"{self.street}, {self.city}, {self.country}")


@dataclass
class PhoneNumber:
    """Uluslararası telefon numarası"""
    country_code: str
    national_number: str
    extension: Optional[str] = None
    
    def format_international(self) -> str:
        """Uluslararası formatta telefon numarası"""
        return f"+{self.country_code} {self.national_number}"
    
    def format_national(self, country_code: str) -> str:
        """Ulusal formatta telefon numarası"""
        # Ülkeye göre formatlama mantığı
        if country_code == 'TR':
            return f"0{self.national_number}"
        elif country_code == 'US':
            return f"({self.national_number[:3]}) {self.national_number[3:6]}-{self.national_number[6:]}"
        else:
            return self.format_international()


class LocalizationManager:
    """Yerelleştirme yöneticisi"""
    
    def __init__(self):
        self.translations: Dict[str, gettext.GNUTranslations] = {}
        self.current_locale: Dict[str, Locale] = {}
        self.regional_settings: Dict[str, RegionalSettings] = {}
        
        # Varsayılan ayarlar
        self.default_settings = RegionalSettings(
            language=LanguageCode.TURKISH,
            currency=CurrencyCode.TURKISH_LIRA,
            timezone="Europe/Istanbul",
            date_format="dd.MM.yyyy",
            time_format="HH:mm",
            number_format="#,##0.###",
            measurement_system="metric",
            address_format="TR",
            phone_format="TR"
        )
        
        # Dil dosyalarını yükle
        self._load_translations()
    
    def _load_translations(self):
        """Çeviri dosyalarını yükle"""
        try:
            # Türkçe
            tr_translation = gettext.translation(
                'messages', 
                localedir='locales',
                languages=['tr'],
                fallback=True
            )
            self.translations['tr'] = tr_translation
            
            # İngilizce
            en_translation = gettext.translation(
                'messages',
                localedir='locales', 
                languages=['en'],
                fallback=True
            )
            self.translations['en'] = en_translation
            
            # Diğer diller için fallback
            for lang in LanguageCode:
                if lang.value not in self.translations:
                    self.translations[lang.value] = gettext.NullTranslations()
            
            logger.info("Çeviri dosyaları yüklendi")
            
        except Exception as e:
            logger.error(f"Çeviri yükleme hatası: {e}")
            # Fallback olarak NullTranslations kullan
            for lang in LanguageCode:
                self.translations[lang.value] = gettext.NullTranslations()
    
    def set_user_locale(self, user_id: str, language: LanguageCode, currency: CurrencyCode = None):
        """Kullanıcı için dil ve para birimi ayarla"""
        try:
            # Locale oluştur
            locale = Locale(language.value)
            self.current_locale[user_id] = locale
            
            # Bölgesel ayarlar
            if user_id not in self.regional_settings:
                self.regional_settings[user_id] = self.default_settings.copy()
            
            self.regional_settings[user_id].language = language
            
            if currency:
                self.regional_settings[user_id].currency = currency
            
            logger.debug(f"Kullanıcı locale ayarlandı: {user_id} -> {language.value}")
            
        except Exception as e:
            logger.error(f"Locale ayarlama hatası: {e}")
    
    def get_user_locale(self, user_id: str) -> Optional[Locale]:
        """Kullanıcının locale'ini al"""
        return self.current_locale.get(user_id)
    
    def get_user_settings(self, user_id: str) -> RegionalSettings:
        """Kullanıcının bölgesel ayarlarını al"""
        return self.regional_settings.get(user_id, self.default_settings)
    
    def translate(self, user_id: str, message: str, **kwargs) -> str:
        """Mesajı çevir"""
        try:
            settings = self.get_user_settings(user_id)
            translation = self.translations.get(settings.language.value, self.translations['tr'])
            
            # Mesajı çevir
            translated = translation.gettext(message)
            
            # Format parametrelerini uygula
            if kwargs:
                try:
                    translated = translated.format(**kwargs)
                except KeyError as e:
                    logger.warning(f"Çeviri format hatası: {e}")
            
            return translated
            
        except Exception as e:
            logger.error(f"Çeviri hatası: {e}")
            return message.format(**kwargs) if kwargs else message
    
    def translate_plural(self, user_id: str, singular: str, plural: str, count: int, **kwargs) -> str:
        """Çoğul mesajı çevir"""
        try:
            settings = self.get_user_settings(user_id)
            translation = self.translations.get(settings.language.value, self.translations['tr'])
            
            translated = translation.ngettext(singular, plural, count)
            
            if kwargs:
                kwargs['count'] = count
                translated = translated.format(**kwargs)
            
            return translated
            
        except Exception as e:
            logger.error(f"Çoğul çeviri hatası: {e}")
            return singular if count == 1 else plural.format(count=count, **kwargs)
    
    def format_currency(
        self, 
        user_id: str, 
        amount: float, 
        custom_currency: CurrencyCode = None
    ) -> str:
        """Para birimini biçimlendir"""
        try:
            settings = self.get_user_settings(user_id)
            currency = custom_currency or settings.currency
            locale = self.current_locale.get(user_id, self.current_locale.get('tr'))
            
            return format_currency(amount, currency.value, locale=locale)
            
        except Exception as e:
            logger.error(f"Para birimi formatlama hatası: {e}")
            return f"{amount} {currency.value if 'currency' in locals() else 'TRY'}"
    
    def format_number(self, user_id: str, number: float, decimal_places: int = 2) -> str:
        """Sayıyı biçimlendir"""
        try:
            settings = self.get_user_settings(user_id)
            locale = self.current_locale.get(user_id, self.current_locale.get('tr'))
            
            return format_decimal(number, format=f"#,##0.{ '0' * decimal_places }", locale=locale)
            
        except Exception as e:
            logger.error(f"Sayı formatlama hatası: {e}")
            return f"{number:.{decimal_places}f}"
    
    def format_date(
        self, 
        user_id: str, 
        date: datetime, 
        date_only: bool = True
    ) -> str:
        """Tarihi biçimlendir"""
        try:
            settings = self.get_user_settings(user_id)
            locale = self.current_locale.get(user_id, self.current_locale.get('tr'))
            
            if date_only:
                return format_date(date, format=settings.date_format, locale=locale)
            else:
                return format_datetime(date, locale=locale)
                
        except Exception as e:
            logger.error(f"Tarih formatlama hatası: {e}")
            return date.strftime("%d.%m.%Y")
    
    def format_time(self, user_id: str, time: datetime) -> str:
        """Saati biçimlendir"""
        try:
            settings = self.get_user_settings(user_id)
            locale = self.current_locale.get(user_id, self.current_locale.get('tr'))
            
            return format_time(time, format=settings.time_format, locale=locale)
            
        except Exception as e:
            logger.error(f"Saat formatlama hatası: {e}")
            return time.strftime("%H:%M")
    
    def format_phone_number(self, user_id: str, phone_number: PhoneNumber) -> str:
        """Telefon numarasını biçimlendir"""
        try:
            settings = self.get_user_settings(user_id)
            return phone_number.format_national(settings.phone_format)
            
        except Exception as e:
            logger.error(f"Telefon formatlama hatası: {e}")
            return phone_number.format_international()
    
    def convert_measurement(
        self, 
        user_id: str, 
        value: float, 
        from_unit: str, 
        to_unit: str
    ) -> float:
        """Ölçü birimi dönüşümü"""
        try:
            settings = self.get_user_settings(user_id)
            
            # Metrik sistemdeyse ve değer imperial birimdeyse dönüştür
            if settings.measurement_system == 'metric' and from_unit in ['mi', 'ft', 'lb']:
                return self._imperial_to_metric(value, from_unit)
            
            # Imperial sistemdeyse ve değer metrik birimdeyse dönüştür
            elif settings.measurement_system == 'imperial' and from_unit in ['km', 'm', 'kg']:
                return self._metric_to_imperial(value, from_unit)
            
            return value
            
        except Exception as e:
            logger.error(f"Ölçü birimi dönüşüm hatası: {e}")
            return value
    
    def _imperial_to_metric(self, value: float, unit: str) -> float:
        """Imperial'den metriğe dönüşüm"""
        conversions = {
            'mi': value * 1.60934,  # mil -> km
            'ft': value * 0.3048,   # feet -> metre
            'lb': value * 0.453592  # pound -> kg
        }
        return conversions.get(unit, value)
    
    def _metric_to_imperial(self, value: float, unit: str) -> float:
        """Metrikten imperial'e dönüşüm"""
        conversions = {
            'km': value / 1.60934,  # km -> mil
            'm': value / 0.3048,    # metre -> feet
            'kg': value / 0.453592  # kg -> pound
        }
        return conversions.get(unit, value)
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Desteklenen dilleri al"""
        languages = []
        for lang in LanguageCode:
            languages.append({
                'code': lang.value,
                'name': self._get_language_name(lang),
                'native_name': self._get_native_language_name(lang)
            })
        return languages
    
    def get_supported_currencies(self) -> List[Dict[str, str]]:
        """Desteklenen para birimlerini al"""
        currencies = []
        for curr in CurrencyCode:
            currencies.append({
                'code': curr.value,
                'name': self._get_currency_name(curr),
                'symbol': self._get_currency_symbol(curr)
            })
        return currencies
    
    def _get_language_name(self, language: LanguageCode) -> str:
        """Dil adını al"""
        names = {
            LanguageCode.TURKISH: "Turkish",
            LanguageCode.ENGLISH: "English",
            LanguageCode.GERMAN: "German",
            LanguageCode.FRENCH: "French",
            LanguageCode.SPANISH: "Spanish",
            LanguageCode.ARABIC: "Arabic",
            LanguageCode.RUSSIAN: "Russian",
            LanguageCode.CHINESE: "Chinese",
            LanguageCode.JAPANESE: "Japanese"
        }
        return names.get(language, language.value)
    
    def _get_native_language_name(self, language: LanguageCode) -> str:
        """Dilin yerel adını al"""
        names = {
            LanguageCode.TURKISH: "Türkçe",
            LanguageCode.ENGLISH: "English",
            LanguageCode.GERMAN: "Deutsch",
            LanguageCode.FRENCH: "Français",
            LanguageCode.SPANISH: "Español",
            LanguageCode.ARABIC: "العربية",
            LanguageCode.RUSSIAN: "Русский",
            LanguageCode.CHINESE: "中文",
            LanguageCode.JAPANESE: "日本語"
        }
        return names.get(language, language.value)
    
    def _get_currency_name(self, currency: CurrencyCode) -> str:
        """Para birimi adını al"""
        names = {
            CurrencyCode.TURKISH_LIRA: "Turkish Lira",
            CurrencyCode.US_DOLLAR: "US Dollar",
            CurrencyCode.EURO: "Euro",
            CurrencyCode.BRITISH_POUND: "British Pound",
            CurrencyCode.SWISS_FRANC: "Swiss Franc",
            CurrencyCode.RUSSIAN_RUBLE: "Russian Ruble",
            CurrencyCode.CHINESE_YUAN: "Chinese Yuan",
            CurrencyCode.JAPANESE_YEN: "Japanese Yen",
            CurrencyCode.SAUDI_RIYAL: "Saudi Riyal"
        }
        return names.get(currency, currency.value)
    
    def _get_currency_symbol(self, currency: CurrencyCode) -> str:
        """Para birimi sembolünü al"""
        symbols = {
            CurrencyCode.TURKISH_LIRA: "₺",
            CurrencyCode.US_DOLLAR: "$",
            CurrencyCode.EURO: "€",
            CurrencyCode.BRITISH_POUND: "£",
            CurrencyCode.SWISS_FRANC: "CHF",
            CurrencyCode.RUSSIAN_RUBLE: "₽",
            CurrencyCode.CHINESE_YUAN: "¥",
            CurrencyCode.JAPANESE_YEN: "¥",
            CurrencyCode.SAUDI_RIYAL: "﷼"
        }
        return symbols.get(currency, currency.value)


class InternationalAddressValidator:
    """Uluslararası adres doğrulama"""
    
    def __init__(self):
        self.country_formats = {
            'TR': {
                'required': ['street', 'city', 'postal_code'],
                'optional': ['district', 'building_number'],
                'postal_code_pattern': r'^\d{5}$'
            },
            'US': {
                'required': ['street', 'city', 'state_province', 'postal_code'],
                'optional': ['apartment'],
                'postal_code_pattern': r'^\d{5}(-\d{4})?$'
            },
            'DE': {
                'required': ['street', 'postal_code', 'city'],
                'optional': ['building_number'],
                'postal_code_pattern': r'^\d{5}$'
            }
        }
    
    def validate_address(self, address: Address, country_code: str) -> Dict[str, Any]:
        """Adresi doğrula"""
        if country_code not in self.country_formats:
            return {
                'valid': False,
                'errors': [f"Ülke kodu desteklenmiyor: {country_code}"]
            }
        
        format_config = self.country_formats[country_code]
        errors = []
        
        # Gerekli alan kontrolü
        for field in format_config['required']:
            if not getattr(address, field, None):
                errors.append(f"{field} alanı zorunludur")
        
        # Posta kodu formatı kontrolü
        if address.postal_code and 'postal_code_pattern' in format_config:
            import re
            if not re.match(format_config['postal_code_pattern'], address.postal_code):
                errors.append("Geçersiz posta kodu formatı")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


# Global instances
localization_manager = LocalizationManager()
address_validator = InternationalAddressValidator()


# Yardımcı fonksiyonlar
def get_user_localization(user_id: str) -> LocalizationManager:
    """Kullanıcı için yerelleştirme yöneticisi al"""
    return localization_manager


def format_distance_for_user(user_id: str, distance_km: float) -> str:
    """Kullanıcı için mesafeyi biçimlendir"""
    settings = localization_manager.get_user_settings(user_id)
    
    if settings.measurement_system == 'imperial':
        distance_mi = distance_km * 0.621371
        return f"{distance_mi:.1f} mi"
    else:
        return f"{distance_km:.1f} km"


def format_weight_for_user(user_id: str, weight_kg: float) -> str:
    """Kullanıcı için ağırlığı biçimlendir"""
    settings = localization_manager.get_user_settings(user_id)
    
    if settings.measurement_system == 'imperial':
        weight_lb = weight_kg * 2.20462
        return f"{weight_lb:.1f} lb"
    else:
        return f"{weight_kg:.1f} kg"


def get_business_hours_for_timezone(timezone: str) -> Dict[str, Any]:
    """Zaman dilimine göre iş saatlerini al"""
    # Zaman dilimine göre iş saatleri
    business_hours = {
        'Europe/Istanbul': {
            'timezone': 'Europe/Istanbul',
            'business_start': '09:00',
            'business_end': '18:00',
            'weekend_work': False,
            'holidays': ['2024-01-01', '2024-04-23', '2024-05-01']
        },
        'America/New_York': {
            'timezone': 'America/New_York',
            'business_start': '09:00',
            'business_end': '17:00',
            'weekend_work': False,
            'holidays': ['2024-01-01', '2024-07-04', '2024-12-25']
        },
        'Europe/London': {
            'timezone': 'Europe/London',
            'business_start': '08:00',
            'business_end': '17:00',
            'weekend_work': False,
            'holidays': ['2024-01-01', '2024-04-01', '2024-12-25']
        }
    }
    
    return business_hours.get(timezone, business_hours['Europe/Istanbul'])


def is_holiday_for_timezone(date: datetime, timezone: str) -> bool:
    """Zaman dilimi için tatil günü kontrolü"""
    business_hours = get_business_hours_for_timezone(timezone)
    date_str = date.strftime('%Y-%m-%d')
    return date_str in business_hours.get('holidays', [])


def get_localized_delivery_estimate(
    user_id: str, 
    base_duration_minutes: int,
    pickup_timezone: str,
    delivery_timezone: str
) -> Dict[str, Any]:
    """Yerelleştirilmiş teslimat tahmini"""
    settings = localization_manager.get_user_settings(user_id)
    
    # Zaman dilimi farkını hesapla
    from zoneinfo import ZoneInfo
    pickup_tz = ZoneInfo(pickup_timezone)
    delivery_tz = ZoneInfo(delivery_timezone)
    user_tz = ZoneInfo(settings.timezone)
    
    # Teslimat süresini hesapla
    delivery_time = datetime.now(pickup_tz) + timedelta(minutes=base_duration_minutes)
    
    # Kullanıcının zaman dilimine çevir
    user_delivery_time = delivery_time.astimezone(user_tz)
    
    return {
        'estimated_delivery_time': user_delivery_time,
        'timezone': settings.timezone,
        'formatted_date': localization_manager.format_date(user_id, user_delivery_time),
        'formatted_time': localization_manager.format_time(user_id, user_delivery_time),
        'is_business_hours': is_business_hours(user_delivery_time, settings.timezone)
    }


def is_business_hours(date_time: datetime, timezone: str) -> bool:
    """İş saatleri içinde mi?"""
    business_hours = get_business_hours_for_timezone(timezone)
    
    # Hafta sonu kontrolü
    if date_time.weekday() >= 5 and not business_hours.get('weekend_work', False):
        return False
    
    # Tatil kontrolü
    if is_holiday_for_timezone(date_time, timezone):
        return False
    
    # Saat kontrolü
    time_str = date_time.strftime('%H:%M')
    business_start = business_hours['business_start']
    business_end = business_hours['business_end']
    
    return business_start <= time_str <= business_end


# Dil dosyası örnek yapısı
LANGUAGE_FILES_STRUCTURE = {
    "locales/tr/LC_MESSAGES/messages.po": """
# Turkish translations
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Welcome to LOOP Logistics"
msgstr "LOOP Lojistiğe Hoş Geldiniz"

msgid "Order created successfully"
msgstr "Sipariş başarıyla oluşturuldu"

msgid "Courier assigned"
msgstr "Kurye atandı"

msgid "Delivery completed"
msgstr "Teslimat tamamlandı"

msgid "You have {count} new order"
msgid_plural "You have {count} new orders"
msgstr[0] "{count} yeni siparişiniz var"
msgstr[1] "{count} yeni siparişiniz var"
""",
    
    "locales/en/LC_MESSAGES/messages.po": """
# English translations
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Welcome to LOOP Logistics"
msgstr "Welcome to LOOP Logistics"

msgid "Order created successfully"
msgstr "Order created successfully"

msgid "Courier assigned"
msgstr "Courier assigned"

msgid "Delivery completed"
msgstr "Delivery completed"

msgid "You have {count} new order"
msgid_plural "You have {count} new orders"
msgstr[0] "You have {count} new order"
msgstr[1] "You have {count} new orders"
"""
}