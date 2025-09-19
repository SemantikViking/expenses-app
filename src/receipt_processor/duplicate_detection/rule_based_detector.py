"""
Rule-based duplicate detector for Receipt Processing Application.

This module provides rule-based duplicate detection using various matching criteria.
"""

import time
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from loguru import logger

from .base import (
    BaseDuplicateDetector, DuplicateMatch, DuplicateDetectionResult, 
    DuplicateDetectionConfig, DuplicateType, MatchCriteria
)
from ..models import ReceiptData


class RuleBasedDetector(BaseDuplicateDetector):
    """Rule-based duplicate detector using multiple criteria."""
    
    def __init__(self, config: Optional[DuplicateDetectionConfig] = None):
        super().__init__(config)
        logger.info("RuleBasedDetector initialized")
    
    async def detect_duplicates(
        self,
        receipts: List[ReceiptData],
        reference_receipts: Optional[List[ReceiptData]] = None
    ) -> DuplicateDetectionResult:
        """Detect duplicates using rule-based matching."""
        start_time = time.time()
        
        try:
            if not receipts:
                return DuplicateDetectionResult(
                    success=True,
                    duplicates_found=0,
                    processing_time=time.time() - start_time
                )
            
            # Use receipts as reference if no reference receipts provided
            reference = reference_receipts or receipts
            matches = []
            processed_pairs: Set[tuple] = set()
            
            # Compare each receipt with reference receipts
            for i, receipt in enumerate(receipts):
                for j, ref_receipt in enumerate(reference):
                    # Skip self-comparison and already processed pairs
                    if receipt == ref_receipt or (receipt, ref_receipt) in processed_pairs:
                        continue
                    
                    # Check for duplicates
                    match = await self._check_receipts_for_duplicate(receipt, ref_receipt)
                    if match:
                        matches.append(match)
                        processed_pairs.add((receipt, ref_receipt))
                        processed_pairs.add((ref_receipt, receipt))
            
            # Remove duplicate matches (same pair detected multiple times)
            unique_matches = self._deduplicate_matches(matches)
            
            return DuplicateDetectionResult(
                success=True,
                duplicates_found=len(unique_matches),
                matches=unique_matches,
                processing_time=time.time() - start_time,
                metadata={
                    "total_receipts": len(receipts),
                    "reference_receipts": len(reference),
                    "comparisons_made": len(processed_pairs)
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Rule-based duplicate detection failed: {e}")
            
            return DuplicateDetectionResult(
                success=False,
                error_message=str(e),
                error_code="DETECTION_ERROR",
                processing_time=processing_time
            )
    
    async def check_duplicate(
        self,
        receipt: ReceiptData,
        reference_receipts: List[ReceiptData]
    ) -> List[DuplicateMatch]:
        """Check if a single receipt is a duplicate of any reference receipts."""
        matches = []
        
        for ref_receipt in reference_receipts:
            if receipt == ref_receipt:
                continue
            
            match = await self._check_receipts_for_duplicate(receipt, ref_receipt)
            if match:
                matches.append(match)
        
        return matches
    
    async def _check_receipts_for_duplicate(
        self, 
        receipt1: ReceiptData, 
        receipt2: ReceiptData
    ) -> Optional[DuplicateMatch]:
        """Check if two receipts are duplicates."""
        try:
            # Calculate similarity scores for different criteria
            similarities = {}
            match_criteria = []
            
            # Vendor name similarity
            if receipt1.vendor_name and receipt2.vendor_name:
                vendor_sim = self._calculate_vendor_similarity(
                    receipt1.vendor_name, 
                    receipt2.vendor_name
                )
                similarities['vendor'] = vendor_sim
                if vendor_sim >= self.config.vendor_fuzzy_threshold:
                    match_criteria.append(MatchCriteria.VENDOR_NAME)
            
            # Amount similarity
            if receipt1.total_amount and receipt2.total_amount:
                amount_sim = self._calculate_amount_similarity(
                    receipt1.total_amount, 
                    receipt2.total_amount
                )
                similarities['amount'] = amount_sim
                if amount_sim >= 0.8:  # High threshold for amount matching
                    match_criteria.append(MatchCriteria.AMOUNT)
            
            # Date similarity
            if receipt1.transaction_date and receipt2.transaction_date:
                date_sim = self._calculate_date_similarity(
                    receipt1.transaction_date, 
                    receipt2.transaction_date
                )
                similarities['date'] = date_sim
                if date_sim >= 0.8:  # High threshold for date matching
                    match_criteria.append(MatchCriteria.DATE)
            
            # Receipt number similarity
            if receipt1.receipt_number and receipt2.receipt_number:
                number_sim = self._calculate_receipt_number_similarity(
                    receipt1.receipt_number, 
                    receipt2.receipt_number
                )
                similarities['receipt_number'] = number_sim
                if number_sim >= 0.9:  # Very high threshold for receipt number
                    match_criteria.append(MatchCriteria.RECEIPT_NUMBER)
            
            # Text similarity (if available)
            if (receipt1.raw_extraction_text and receipt2.raw_extraction_text and 
                self.config.use_text_similarity):
                text_sim = self._calculate_text_similarity(
                    receipt1.raw_extraction_text, 
                    receipt2.raw_extraction_text
                )
                similarities['text'] = text_sim
                if text_sim >= self.config.text_similarity_threshold:
                    match_criteria.append(MatchCriteria.TEXT_SIMILARITY)
            
            # Calculate overall similarity score
            overall_similarity = self._calculate_overall_similarity(similarities)
            
            # Check if similarity meets threshold for duplicate detection
            if overall_similarity >= self.config.suspicious_match_threshold:
                # Determine duplicate type
                duplicate_type = self._determine_duplicate_type(overall_similarity)
                
                # Create match
                match = DuplicateMatch(
                    match_id=self._create_match_id(
                        getattr(receipt1, 'receipt_id', str(id(receipt1))),
                        getattr(receipt2, 'receipt_id', str(id(receipt2)))
                    ),
                    receipt_id_1=getattr(receipt1, 'receipt_id', str(id(receipt1))),
                    receipt_id_2=getattr(receipt2, 'receipt_id', str(id(receipt2))),
                    duplicate_type=duplicate_type,
                    confidence=overall_similarity,
                    match_criteria=match_criteria,
                    similarity_score=overall_similarity,
                    differences=self._find_differences(receipt1, receipt2)
                )
                
                logger.debug(f"Found duplicate match: {match.match_id} (similarity: {overall_similarity:.3f})")
                return match
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking receipts for duplicate: {e}")
            return None
    
    def _calculate_overall_similarity(self, similarities: Dict[str, float]) -> float:
        """Calculate overall similarity score from individual criteria."""
        if not similarities:
            return 0.0
        
        # Weighted average based on configuration
        weighted_sum = 0.0
        total_weight = 0.0
        
        # Vendor similarity
        if 'vendor' in similarities:
            weighted_sum += similarities['vendor'] * self.config.vendor_weight
            total_weight += self.config.vendor_weight
        
        # Amount similarity
        if 'amount' in similarities:
            weighted_sum += similarities['amount'] * self.config.amount_weight
            total_weight += self.config.amount_weight
        
        # Date similarity
        if 'date' in similarities:
            weighted_sum += similarities['date'] * self.config.date_weight
            total_weight += self.config.date_weight
        
        # Receipt number similarity
        if 'receipt_number' in similarities:
            weighted_sum += similarities['receipt_number'] * self.config.receipt_number_weight
            total_weight += self.config.receipt_number_weight
        
        # Text similarity
        if 'text' in similarities:
            weighted_sum += similarities['text'] * 0.1  # Fixed weight for text
            total_weight += 0.1
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _deduplicate_matches(self, matches: List[DuplicateMatch]) -> List[DuplicateMatch]:
        """Remove duplicate matches (same pair detected multiple times)."""
        seen_pairs = set()
        unique_matches = []
        
        for match in matches:
            # Create a pair identifier (sorted IDs)
            pair = tuple(sorted([match.receipt_id_1, match.receipt_id_2]))
            
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_matches.append(match)
            else:
                # If we've seen this pair before, keep the match with higher confidence
                existing_match = next(
                    (m for m in unique_matches 
                     if tuple(sorted([m.receipt_id_1, m.receipt_id_2])) == pair), 
                    None
                )
                
                if existing_match and match.confidence > existing_match.confidence:
                    # Replace with higher confidence match
                    unique_matches.remove(existing_match)
                    unique_matches.append(match)
        
        return unique_matches
    
    def get_duplicate_groups(self, matches: List[DuplicateMatch]) -> List[List[str]]:
        """Group receipts into duplicate groups based on matches."""
        # Create a graph of connected receipts
        graph = {}
        
        for match in matches:
            receipt1 = match.receipt_id_1
            receipt2 = match.receipt_id_2
            
            if receipt1 not in graph:
                graph[receipt1] = set()
            if receipt2 not in graph:
                graph[receipt2] = set()
            
            graph[receipt1].add(receipt2)
            graph[receipt2].add(receipt1)
        
        # Find connected components using DFS
        visited = set()
        groups = []
        
        def dfs(receipt_id, group):
            if receipt_id in visited:
                return
            visited.add(receipt_id)
            group.append(receipt_id)
            
            for neighbor in graph.get(receipt_id, []):
                dfs(neighbor, group)
        
        for receipt_id in graph:
            if receipt_id not in visited:
                group = []
                dfs(receipt_id, group)
                if len(group) > 1:  # Only include groups with multiple receipts
                    groups.append(group)
        
        return groups
    
    def get_duplicate_statistics(self, matches: List[DuplicateMatch]) -> Dict[str, Any]:
        """Get statistics about duplicate matches."""
        if not matches:
            return {
                "total_matches": 0,
                "exact_matches": 0,
                "similar_matches": 0,
                "suspicious_matches": 0,
                "partial_matches": 0,
                "average_confidence": 0.0,
                "criteria_usage": {}
            }
        
        # Count by duplicate type
        type_counts = {}
        for match in matches:
            type_counts[match.duplicate_type] = type_counts.get(match.duplicate_type, 0) + 1
        
        # Count criteria usage
        criteria_usage = {}
        for match in matches:
            for criteria in match.match_criteria:
                criteria_usage[criteria] = criteria_usage.get(criteria, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(match.confidence for match in matches) / len(matches)
        
        return {
            "total_matches": len(matches),
            "exact_matches": type_counts.get(DuplicateType.EXACT, 0),
            "similar_matches": type_counts.get(DuplicateType.SIMILAR, 0),
            "suspicious_matches": type_counts.get(DuplicateType.SUSPICIOUS, 0),
            "partial_matches": type_counts.get(DuplicateType.PARTIAL, 0),
            "average_confidence": avg_confidence,
            "criteria_usage": criteria_usage
        }
