"""
Language detector for Receipt Processing Application.

This module provides language detection capabilities for receipt text.
"""

import time
import re
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
from loguru import logger

from .base import BaseLanguageProcessor, LanguageCode, LanguageDetectionResult, LanguageConfig


class LanguageDetector(BaseLanguageProcessor):
    """Language detector using multiple detection methods."""
    
    def __init__(self, config: Optional[LanguageConfig] = None):
        super().__init__(config)
        self._character_patterns = self._load_character_patterns()
        self._common_words = self._load_common_words()
        self._currency_symbols = self._load_currency_symbols()
        
        logger.info(f"LanguageDetector initialized with {len(self.config.supported_languages)} languages")
    
    async def detect_language(self, text: str) -> LanguageDetectionResult:
        """Detect the language of the given text."""
        start_time = time.time()
        
        try:
            if not text or not text.strip():
                return LanguageDetectionResult(
                    detected_language=LanguageCode.UNKNOWN,
                    confidence=0.0,
                    detection_method="empty_text",
                    processing_time=time.time() - start_time
                )
            
            # Use multiple detection methods
            detection_results = []
            
            # Character pattern detection
            char_result = self._detect_by_character_patterns(text)
            if char_result:
                detection_results.append(char_result)
            
            # Common words detection
            word_result = self._detect_by_common_words(text)
            if word_result:
                detection_results.append(word_result)
            
            # Currency symbols detection
            currency_result = self._detect_by_currency_symbols(text)
            if currency_result:
                detection_results.append(currency_result)
            
            # Date format detection
            date_result = self._detect_by_date_formats(text)
            if date_result:
                detection_results.append(date_result)
            
            # Combine results
            final_result = self._combine_detection_results(detection_results)
            
            processing_time = time.time() - start_time
            
            return LanguageDetectionResult(
                detected_language=final_result['language'],
                confidence=final_result['confidence'],
                alternative_languages=final_result.get('alternatives', []),
                detection_method=final_result.get('method', 'combined'),
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Language detection failed: {e}")
            
            return LanguageDetectionResult(
                detected_language=LanguageCode.UNKNOWN,
                confidence=0.0,
                detection_method="error",
                processing_time=processing_time
            )
    
    def _detect_by_character_patterns(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect language using character patterns."""
        if not text:
            return None
        
        scores = {}
        
        for language, patterns in self._character_patterns.items():
            if language not in self.config.supported_languages:
                continue
            
            score = 0
            total_chars = len(text)
            
            for pattern, weight in patterns.items():
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += (matches / total_chars) * weight if total_chars > 0 else 0
            
            scores[language] = score
        
        if not scores:
            return None
        
        best_language = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_language])
        
        return {
            'language': best_language,
            'confidence': confidence,
            'method': 'character_patterns',
            'scores': scores
        }
    
    def _detect_by_common_words(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect language using common words."""
        if not text:
            return None
        
        # Normalize text
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return None
        
        scores = {}
        
        for language, word_list in self._common_words.items():
            if language not in self.config.supported_languages:
                continue
            
            matches = sum(1 for word in words if word in word_list)
            score = matches / len(words) if words else 0
            scores[language] = score
        
        if not scores:
            return None
        
        best_language = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_language])
        
        return {
            'language': best_language,
            'confidence': confidence,
            'method': 'common_words',
            'scores': scores
        }
    
    def _detect_by_currency_symbols(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect language using currency symbols."""
        if not text:
            return None
        
        scores = {}
        
        for language, symbols in self._currency_symbols.items():
            if language not in self.config.supported_languages:
                continue
            
            score = 0
            for symbol in symbols:
                if symbol in text:
                    score += 1
            
            scores[language] = score
        
        if not scores or max(scores.values()) == 0:
            return None
        
        best_language = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_language] / 3)  # Normalize to 0-1
        
        return {
            'language': best_language,
            'confidence': confidence,
            'method': 'currency_symbols',
            'scores': scores
        }
    
    def _detect_by_date_formats(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect language using date formats."""
        if not text:
            return None
        
        scores = {}
        
        for language, formats in self.config.date_formats_by_language.items():
            if language not in self.config.supported_languages:
                continue
            
            score = 0
            for date_format in formats:
                # Look for date patterns in text
                pattern = self._date_format_to_regex(date_format)
                matches = len(re.findall(pattern, text))
                score += matches
            
            scores[language] = score
        
        if not scores or max(scores.values()) == 0:
            return None
        
        best_language = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_language] / 2)  # Normalize to 0-1
        
        return {
            'language': best_language,
            'confidence': confidence,
            'method': 'date_formats',
            'scores': scores
        }
    
    def _combine_detection_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple detection results."""
        if not results:
            return {
                'language': LanguageCode.UNKNOWN,
                'confidence': 0.0,
                'method': 'none'
            }
        
        # Weight different methods
        method_weights = {
            'character_patterns': 0.3,
            'common_words': 0.4,
            'currency_symbols': 0.2,
            'date_formats': 0.1
        }
        
        combined_scores = {}
        
        for result in results:
            language = result['language']
            confidence = result['confidence']
            method = result['method']
            weight = method_weights.get(method, 0.1)
            
            if language not in combined_scores:
                combined_scores[language] = 0
            
            combined_scores[language] += confidence * weight
        
        if not combined_scores:
            return {
                'language': LanguageCode.UNKNOWN,
                'confidence': 0.0,
                'method': 'combined'
            }
        
        # Find best language
        best_language = max(combined_scores, key=combined_scores.get)
        best_confidence = combined_scores[best_language]
        
        # Create alternatives
        alternatives = []
        for language, score in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[1:4]:
            if score > 0.1:  # Only include alternatives with reasonable confidence
                alternatives.append({
                    'language': language,
                    'confidence': score
                })
        
        return {
            'language': best_language,
            'confidence': min(1.0, best_confidence),
            'method': 'combined',
            'alternatives': alternatives,
            'all_scores': combined_scores
        }
    
    def _load_character_patterns(self) -> Dict[LanguageCode, Dict[str, float]]:
        """Load character patterns for different languages."""
        return {
            LanguageCode.ENGLISH: {
                r'[a-zA-Z]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3
            },
            LanguageCode.SPANISH: {
                r'[a-zA-Záéíóúñü]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?¿¡]': 0.3,
                r'ñ': 0.8,
                r'[áéíóú]': 0.6
            },
            LanguageCode.FRENCH: {
                r'[a-zA-Zàâäéèêëïîôöùûüÿç]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3,
                r'[àâäéèêëïîôöùûüÿç]': 0.6
            },
            LanguageCode.GERMAN: {
                r'[a-zA-Zäöüß]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3,
                r'[äöüß]': 0.6
            },
            LanguageCode.ITALIAN: {
                r'[a-zA-Zàèéìíîòóù]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3,
                r'[àèéìíîòóù]': 0.6
            },
            LanguageCode.PORTUGUESE: {
                r'[a-zA-Zàáâãéêíóôõúç]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3,
                r'[àáâãéêíóôõúç]': 0.6
            },
            LanguageCode.DUTCH: {
                r'[a-zA-Zàáâäéèêëïíîôöùúûüÿ]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3,
                r'[àáâäéèêëïíîôöùúûüÿ]': 0.6
            },
            LanguageCode.RUSSIAN: {
                r'[а-яё]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3
            },
            LanguageCode.CHINESE_SIMPLIFIED: {
                r'[\u4e00-\u9fff]': 1.0,
                r'[0-9]': 0.5,
                r'[，。！？]': 0.3
            },
            LanguageCode.CHINESE_TRADITIONAL: {
                r'[\u4e00-\u9fff]': 1.0,
                r'[0-9]': 0.5,
                r'[，。！？]': 0.3
            },
            LanguageCode.JAPANESE: {
                r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]': 1.0,
                r'[0-9]': 0.5,
                r'[，。！？]': 0.3
            },
            LanguageCode.KOREAN: {
                r'[\uac00-\ud7af]': 1.0,
                r'[0-9]': 0.5,
                r'[，。！？]': 0.3
            },
            LanguageCode.ARABIC: {
                r'[\u0600-\u06ff]': 1.0,
                r'[0-9]': 0.5,
                r'[،.؟!]': 0.3
            },
            LanguageCode.HINDI: {
                r'[\u0900-\u097f]': 1.0,
                r'[0-9]': 0.5,
                r'[.,!?]': 0.3
            }
        }
    
    def _load_common_words(self) -> Dict[LanguageCode, set]:
        """Load common words for different languages."""
        return {
            LanguageCode.ENGLISH: {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'total', 'amount', 'price', 'cost', 'tax', 'subtotal', 'receipt', 'invoice',
                'date', 'time', 'cash', 'card', 'payment', 'thank', 'you'
            },
            LanguageCode.SPANISH: {
                'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo',
                'total', 'cantidad', 'precio', 'costo', 'impuesto', 'subtotal', 'recibo', 'factura',
                'fecha', 'hora', 'efectivo', 'tarjeta', 'pago', 'gracias'
            },
            LanguageCode.FRENCH: {
                'le', 'la', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que',
                'total', 'montant', 'prix', 'coût', 'taxe', 'sous-total', 'reçu', 'facture',
                'date', 'heure', 'espèces', 'carte', 'paiement', 'merci'
            },
            LanguageCode.GERMAN: {
                'der', 'die', 'das', 'und', 'in', 'zu', 'den', 'von', 'mit', 'sich', 'des',
                'gesamt', 'betrag', 'preis', 'kosten', 'steuer', 'zwischensumme', 'beleg', 'rechnung',
                'datum', 'zeit', 'bargeld', 'karte', 'zahlung', 'danke'
            },
            LanguageCode.ITALIAN: {
                'il', 'la', 'di', 'e', 'a', 'in', 'un', 'è', 'per', 'con', 'da', 'del',
                'totale', 'importo', 'prezzo', 'costo', 'tassa', 'subtotale', 'ricevuta', 'fattura',
                'data', 'ora', 'contanti', 'carta', 'pagamento', 'grazie'
            },
            LanguageCode.PORTUGUESE: {
                'o', 'a', 'de', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma',
                'total', 'valor', 'preço', 'custo', 'imposto', 'subtotal', 'recibo', 'fatura',
                'data', 'hora', 'dinheiro', 'cartão', 'pagamento', 'obrigado'
            },
            LanguageCode.DUTCH: {
                'de', 'het', 'en', 'van', 'in', 'op', 'te', 'voor', 'met', 'aan', 'is', 'dat',
                'totaal', 'bedrag', 'prijs', 'kosten', 'belasting', 'subtotaal', 'bon', 'factuur',
                'datum', 'tijd', 'contant', 'kaart', 'betaling', 'dank'
            },
            LanguageCode.RUSSIAN: {
                'и', 'в', 'не', 'на', 'я', 'быть', 'с', 'он', 'а', 'как', 'по', 'но',
                'итого', 'сумма', 'цена', 'стоимость', 'налог', 'подитог', 'чек', 'счет',
                'дата', 'время', 'наличные', 'карта', 'платеж', 'спасибо'
            },
            LanguageCode.CHINESE_SIMPLIFIED: {
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
                '总计', '金额', '价格', '费用', '税', '小计', '收据', '发票',
                '日期', '时间', '现金', '卡', '支付', '谢谢'
            },
            LanguageCode.CHINESE_TRADITIONAL: {
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
                '總計', '金額', '價格', '費用', '稅', '小計', '收據', '發票',
                '日期', '時間', '現金', '卡', '支付', '謝謝'
            },
            LanguageCode.JAPANESE: {
                'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ',
                '合計', '金額', '価格', '費用', '税', '小計', '領収書', '請求書',
                '日付', '時間', '現金', 'カード', '支払い', 'ありがとう'
            },
            LanguageCode.KOREAN: {
                '의', '이', '가', '을', '를', '에', '에서', '와', '과', '도', '는', '은',
                '총계', '금액', '가격', '비용', '세금', '소계', '영수증', '청구서',
                '날짜', '시간', '현금', '카드', '결제', '감사'
            },
            LanguageCode.ARABIC: {
                'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي', 'كان', 'كانت', 'يكون', 'تكون',
                'المجموع', 'المبلغ', 'السعر', 'التكلفة', 'الضريبة', 'المجموع الفرعي', 'الإيصال', 'الفاتورة',
                'التاريخ', 'الوقت', 'النقد', 'البطاقة', 'الدفع', 'شكرا'
            },
            LanguageCode.HINDI: {
                'का', 'की', 'के', 'में', 'से', 'को', 'पर', 'है', 'हैं', 'था', 'थी', 'थे',
                'कुल', 'राशि', 'कीमत', 'लागत', 'कर', 'उप-योग', 'रसीद', 'बिल',
                'तारीख', 'समय', 'नकद', 'कार्ड', 'भुगतान', 'धन्यवाद'
            }
        }
    
    def _load_currency_symbols(self) -> Dict[LanguageCode, List[str]]:
        """Load currency symbols for different languages."""
        return {
            LanguageCode.ENGLISH: ['$', 'USD', 'US$'],
            LanguageCode.SPANISH: ['€', 'EUR', '€uros'],
            LanguageCode.FRENCH: ['€', 'EUR', 'euros'],
            LanguageCode.GERMAN: ['€', 'EUR', 'Euro'],
            LanguageCode.ITALIAN: ['€', 'EUR', 'euro'],
            LanguageCode.PORTUGUESE: ['€', 'EUR', 'euros'],
            LanguageCode.DUTCH: ['€', 'EUR', 'euro'],
            LanguageCode.RUSSIAN: ['₽', 'RUB', 'руб'],
            LanguageCode.CHINESE_SIMPLIFIED: ['¥', 'CNY', '元'],
            LanguageCode.CHINESE_TRADITIONAL: ['¥', 'TWD', '元'],
            LanguageCode.JAPANESE: ['¥', 'JPY', '円'],
            LanguageCode.KOREAN: ['₩', 'KRW', '원'],
            LanguageCode.ARABIC: ['ر.س', 'SAR', 'ريال'],
            LanguageCode.HINDI: ['₹', 'INR', 'रुपये']
        }
    
    def _date_format_to_regex(self, date_format: str) -> str:
        """Convert date format to regex pattern."""
        # Simple conversion - could be enhanced
        pattern = date_format
        pattern = pattern.replace('%Y', r'\d{4}')
        pattern = pattern.replace('%m', r'\d{1,2}')
        pattern = pattern.replace('%d', r'\d{1,2}')
        pattern = pattern.replace('%B', r'[A-Za-z]+')
        pattern = pattern.replace('%b', r'[A-Za-z]+')
        return pattern
