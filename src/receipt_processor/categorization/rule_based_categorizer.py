"""
Rule-based categorizer for Receipt Processing Application.

This module provides rule-based categorization of receipts using pattern matching.
"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from .base import BaseCategorizer, CategoryRule, ReceiptCategory, CategorizationResult, CategoryType


class RuleBasedCategorizer(BaseCategorizer):
    """Rule-based categorizer using pattern matching."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.min_confidence = config.get('min_confidence', 0.5) if config else 0.5
        self.require_multiple_matches = config.get('require_multiple_matches', False) if config else False
        
        logger.info(f"RuleBasedCategorizer initialized with {len(self._rules)} rules")
    
    async def categorize(
        self, 
        receipt_data: ReceiptData,
        rules: Optional[List[CategoryRule]] = None
    ) -> CategorizationResult:
        """Categorize a receipt using rule-based matching."""
        start_time = time.time()
        
        try:
            rules_to_use = rules or self._rules
            enabled_rules = [rule for rule in rules_to_use if rule.enabled]
            
            if not enabled_rules:
                return CategorizationResult(
                    success=False,
                    error_message="No enabled rules available",
                    error_code="NO_RULES",
                    processing_time=time.time() - start_time
                )
            
            # Find matching rules
            matching_rules = self._find_matching_rules(receipt_data, enabled_rules)
            
            if not matching_rules:
                # No rules matched, return default category
                category = ReceiptCategory(
                    category=CategoryType.OTHER,
                    confidence=0.0,
                    reasoning="No rules matched",
                    subcategory="uncategorized"
                )
                
                return CategorizationResult(
                    success=True,
                    category=category,
                    processing_time=time.time() - start_time,
                    metadata={"matched_rules": 0, "total_rules": len(enabled_rules)}
                )
            
            # Calculate confidence and select best category
            best_category = self._select_best_category(matching_rules, receipt_data)
            
            return CategorizationResult(
                success=True,
                category=best_category,
                processing_time=time.time() - start_time,
                metadata={
                    "matched_rules": len(matching_rules),
                    "total_rules": len(enabled_rules),
                    "rule_details": [rule.rule_id for rule in matching_rules]
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Rule-based categorization failed: {e}")
            
            return CategorizationResult(
                success=False,
                error_message=str(e),
                error_code="CATEGORIZATION_ERROR",
                processing_time=processing_time
            )
    
    def _find_matching_rules(self, receipt_data: ReceiptData, rules: List[CategoryRule]) -> List[CategoryRule]:
        """Find rules that match the receipt data."""
        matching_rules = []
        
        for rule in rules:
            if self._rule_matches(receipt_data, rule):
                matching_rules.append(rule)
                logger.debug(f"Rule '{rule.rule_id}' matched receipt")
        
        return matching_rules
    
    def _rule_matches(self, receipt_data: ReceiptData, rule: CategoryRule) -> bool:
        """Check if a rule matches the receipt data."""
        matches = []
        
        # Check vendor patterns
        if rule.vendor_patterns and receipt_data.vendor_name:
            vendor_match = self._match_vendor_patterns(
                receipt_data.vendor_name, 
                rule.vendor_patterns, 
                rule.case_sensitive
            )
            matches.append(vendor_match)
        
        # Check amount ranges
        if rule.amount_ranges and receipt_data.total_amount:
            amount_match = self._match_amount_ranges(
                receipt_data.total_amount, 
                rule.amount_ranges
            )
            matches.append(amount_match)
        
        # Check keywords in various fields
        if rule.keywords:
            keyword_matches = []
            
            # Check vendor name
            if receipt_data.vendor_name:
                keyword_matches.append(
                    self._match_keywords(
                        receipt_data.vendor_name, 
                        rule.keywords, 
                        rule.case_sensitive
                    )
                )
            
            # Check receipt number
            if receipt_data.receipt_number:
                keyword_matches.append(
                    self._match_keywords(
                        receipt_data.receipt_number, 
                        rule.keywords, 
                        rule.case_sensitive
                    )
                )
            
            # Check raw extraction text
            if receipt_data.raw_extraction_text:
                keyword_matches.append(
                    self._match_keywords(
                        receipt_data.raw_extraction_text, 
                        rule.keywords, 
                        rule.case_sensitive
                    )
                )
            
            if keyword_matches:
                matches.append(any(keyword_matches))
        
        # Check payment methods
        if rule.payment_methods and receipt_data.payment_method:
            payment_match = receipt_data.payment_method.lower() in [
                method.lower() for method in rule.payment_methods
            ]
            matches.append(payment_match)
        
        # Check date ranges
        if rule.date_ranges and receipt_data.transaction_date:
            date_match = self._match_date_ranges(
                receipt_data.transaction_date, 
                rule.date_ranges
            )
            matches.append(date_match)
        
        # Determine if rule matches based on require_all setting
        if not matches:
            return False
        
        if rule.require_all:
            return all(matches)
        else:
            return any(matches)
    
    def _match_date_ranges(self, date: datetime, ranges: List[Dict[str, datetime]]) -> bool:
        """Check if date falls within any range."""
        if not date or not ranges:
            return False
        
        for range_def in ranges:
            start_date = range_def.get('start')
            end_date = range_def.get('end')
            
            if start_date and end_date:
                if start_date <= date <= end_date:
                    return True
            elif start_date:
                if date >= start_date:
                    return True
            elif end_date:
                if date <= end_date:
                    return True
        
        return False
    
    def _select_best_category(self, matching_rules: List[CategoryRule], receipt_data: ReceiptData) -> ReceiptCategory:
        """Select the best category from matching rules."""
        if not matching_rules:
            return ReceiptCategory(
                category=CategoryType.OTHER,
                confidence=0.0,
                reasoning="No matching rules"
            )
        
        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(matching_rules, key=lambda r: r.priority, reverse=True)
        
        # Calculate confidence based on number of matches and rule priorities
        confidence = self._calculate_confidence(matching_rules, receipt_data)
        
        # Select the highest priority rule
        best_rule = sorted_rules[0]
        
        # Create reasoning text
        reasoning_parts = [f"Matched rule: {best_rule.name}"]
        
        if len(matching_rules) > 1:
            reasoning_parts.append(f"({len(matching_rules)} total matches)")
        
        # Add specific match details
        match_details = self._get_match_details(receipt_data, best_rule)
        if match_details:
            reasoning_parts.append(f"Matches: {', '.join(match_details)}")
        
        reasoning = ". ".join(reasoning_parts)
        
        # Determine subcategory
        subcategory = self._determine_subcategory(best_rule, receipt_data)
        
        # Extract tags
        tags = self._extract_tags(best_rule, receipt_data)
        
        return ReceiptCategory(
            category=best_rule.category,
            confidence=confidence,
            matched_rules=[rule.rule_id for rule in matching_rules],
            reasoning=reasoning,
            subcategory=subcategory,
            tags=tags,
            metadata={
                "rule_priorities": [rule.priority for rule in matching_rules],
                "total_matches": len(matching_rules)
            }
        )
    
    def _calculate_confidence(self, matching_rules: List[CategoryRule], receipt_data: ReceiptData) -> float:
        """Calculate confidence score for categorization."""
        if not matching_rules:
            return 0.0
        
        # Base confidence on number of matching rules
        base_confidence = min(0.8, len(matching_rules) * 0.2)
        
        # Boost confidence for high-priority rules
        max_priority = max(rule.priority for rule in matching_rules)
        priority_boost = min(0.2, (max_priority - 50) / 500)  # Normalize priority
        
        # Boost confidence for specific matches
        specificity_boost = 0.0
        for rule in matching_rules:
            if rule.vendor_patterns and receipt_data.vendor_name:
                # Check for exact vendor name matches
                vendor_lower = receipt_data.vendor_name.lower()
                for pattern in rule.vendor_patterns:
                    if pattern.lower() == vendor_lower:
                        specificity_boost += 0.1
                        break
        
        total_confidence = base_confidence + priority_boost + specificity_boost
        return min(1.0, total_confidence)
    
    def _get_match_details(self, receipt_data: ReceiptData, rule: CategoryRule) -> List[str]:
        """Get details about what matched in the rule."""
        details = []
        
        if rule.vendor_patterns and receipt_data.vendor_name:
            for pattern in rule.vendor_patterns:
                if pattern.lower() in receipt_data.vendor_name.lower():
                    details.append(f"vendor pattern: {pattern}")
                    break
        
        if rule.keywords:
            matched_keywords = []
            text_fields = [
                receipt_data.vendor_name,
                receipt_data.receipt_number,
                receipt_data.raw_extraction_text
            ]
            
            for field in text_fields:
                if field:
                    for keyword in rule.keywords:
                        if keyword.lower() in field.lower():
                            matched_keywords.append(keyword)
            
            if matched_keywords:
                details.append(f"keywords: {', '.join(set(matched_keywords))}")
        
        if rule.amount_ranges and receipt_data.total_amount:
            details.append(f"amount: ${receipt_data.total_amount}")
        
        return details
    
    def _determine_subcategory(self, rule: CategoryRule, receipt_data: ReceiptData) -> Optional[str]:
        """Determine subcategory based on rule and receipt data."""
        # This is a simple implementation - could be enhanced with more sophisticated logic
        if rule.category == CategoryType.FOOD_DINING:
            if any(keyword in receipt_data.vendor_name.lower() for keyword in ['restaurant', 'cafe', 'diner']):
                return 'restaurant'
            elif any(keyword in receipt_data.vendor_name.lower() for keyword in ['grocery', 'supermarket', 'market']):
                return 'grocery'
            else:
                return 'dining'
        
        elif rule.category == CategoryType.TRANSPORTATION:
            if any(keyword in receipt_data.vendor_name.lower() for keyword in ['gas', 'fuel', 'station']):
                return 'fuel'
            elif any(keyword in receipt_data.vendor_name.lower() for keyword in ['uber', 'lyft', 'taxi']):
                return 'rideshare'
            else:
                return 'transportation'
        
        elif rule.category == CategoryType.RETAIL_SHOPPING:
            if any(keyword in receipt_data.vendor_name.lower() for keyword in ['amazon', 'ebay', 'online']):
                return 'online'
            else:
                return 'retail'
        
        return None
    
    def _extract_tags(self, rule: CategoryRule, receipt_data: ReceiptData) -> List[str]:
        """Extract tags for the categorized receipt."""
        tags = rule.tags.copy()
        
        # Add category-based tags
        tags.append(rule.category.value)
        
        # Add subcategory tag if available
        subcategory = self._determine_subcategory(rule, receipt_data)
        if subcategory:
            tags.append(subcategory)
        
        # Add amount-based tags
        if receipt_data.total_amount:
            if receipt_data.total_amount < 10:
                tags.append('small_amount')
            elif receipt_data.total_amount > 100:
                tags.append('large_amount')
        
        # Add date-based tags
        if receipt_data.transaction_date:
            weekday = receipt_data.transaction_date.weekday()
            if weekday < 5:  # Monday-Friday
                tags.append('weekday')
            else:  # Weekend
                tags.append('weekend')
        
        return list(set(tags))  # Remove duplicates
    
    def add_rule(self, rule: CategoryRule) -> None:
        """Add a categorization rule."""
        # Check if rule ID already exists
        existing_rule = next((r for r in self._rules if r.rule_id == rule.rule_id), None)
        if existing_rule:
            # Update existing rule
            rule.updated_at = datetime.now()
            index = self._rules.index(existing_rule)
            self._rules[index] = rule
            logger.info(f"Updated rule: {rule.rule_id}")
        else:
            # Add new rule
            self._rules.append(rule)
            logger.info(f"Added rule: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a categorization rule by ID."""
        rule = next((r for r in self._rules if r.rule_id == rule_id), None)
        if rule:
            self._rules.remove(rule)
            logger.info(f"Removed rule: {rule_id}")
            return True
        else:
            logger.warning(f"Rule not found: {rule_id}")
            return False
    
    def get_rules(self) -> List[CategoryRule]:
        """Get all categorization rules."""
        return self._rules.copy()
    
    def get_rules_by_category(self, category: CategoryType) -> List[CategoryRule]:
        """Get rules for a specific category."""
        return [rule for rule in self._rules if rule.category == category]
    
    def get_enabled_rules(self) -> List[CategoryRule]:
        """Get all enabled rules."""
        return [rule for rule in self._rules if rule.enabled]
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule by ID."""
        rule = next((r for r in self._rules if r.rule_id == rule_id), None)
        if rule:
            rule.enabled = False
            rule.updated_at = datetime.now()
            logger.info(f"Disabled rule: {rule_id}")
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule by ID."""
        rule = next((r for r in self._rules if r.rule_id == rule_id), None)
        if rule:
            rule.enabled = True
            rule.updated_at = datetime.now()
            logger.info(f"Enabled rule: {rule_id}")
            return True
        return False
