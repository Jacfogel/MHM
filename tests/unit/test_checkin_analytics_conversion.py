"""
Unit tests for checkin_analytics conversion helper functions.

Tests the score conversion utilities:
- convert_score_100_to_5: Converts 0-100 scale to 1-5 scale
- convert_score_5_to_100: Converts 1-5 scale to 0-100 scale
"""

import pytest
from core.checkin_analytics import CheckinAnalytics


class TestScoreConversion100To5:
    """Test conversion from 0-100 scale to 1-5 scale."""
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_0_to_0(self):
        """Test that 0 converts to 0."""
        result = CheckinAnalytics.convert_score_100_to_5(0)
        assert result == 0.0, "0 should convert to 0.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_negative_to_0(self):
        """Test that negative values convert to 0."""
        result = CheckinAnalytics.convert_score_100_to_5(-10)
        assert result == 0.0, "Negative values should convert to 0.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_100_to_5(self):
        """Test that 100 converts to 5.0."""
        result = CheckinAnalytics.convert_score_100_to_5(100)
        assert result == 5.0, "100 should convert to 5.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_50_to_3(self):
        """Test that 50 converts to 3.0 (middle value)."""
        result = CheckinAnalytics.convert_score_100_to_5(50)
        assert result == 3.0, "50 should convert to 3.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_25_to_2(self):
        """Test that 25 converts to 2.0."""
        result = CheckinAnalytics.convert_score_100_to_5(25)
        assert result == 2.0, "25 should convert to 2.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_75_to_4(self):
        """Test that 75 converts to 4.0."""
        result = CheckinAnalytics.convert_score_100_to_5(75)
        assert result == 4.0, "75 should convert to 4.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_rounds_to_one_decimal(self):
        """Test that results are rounded to 1 decimal place."""
        # 37.5 should convert to 2.5 (37.5 / 25 + 1 = 2.5)
        result = CheckinAnalytics.convert_score_100_to_5(37.5)
        assert result == 2.5, "37.5 should convert to 2.5"
        assert isinstance(result, float), "Result should be float"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_100_to_5_with_non_integer_results(self):
        """Test conversion from 0-100 to 1-5 with non-integer results."""
        # Test various values that produce non-integer results
        test_cases = [
            (32.5, 2.3),   # Should round to 2.3
            (67.5, 3.7),   # Should round to 3.7
            (12.5, 1.5),   # Should round to 1.5
            (97.5, 4.9),   # Should round to 4.9
            (80.0, 4.2),   # Should round to 4.2
            (2.5, 1.1),    # Should round to 1.1
        ]
        
        for score_100, expected_5 in test_cases:
            result = CheckinAnalytics.convert_score_100_to_5(score_100)
            assert result == expected_5, f"{score_100} should convert to {expected_5}, got {result}"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_edge_cases(self):
        """Test edge case values."""
        # Test values just above 0
        result = CheckinAnalytics.convert_score_100_to_5(0.1)
        assert result > 0, "Small positive value should convert to > 0"
        
        # Test values just below 100 (99.9 / 25 + 1 = 4.996, rounds to 5.0)
        result = CheckinAnalytics.convert_score_100_to_5(99.9)
        assert result <= 5.0, "Value just below 100 should convert to <= 5.0"
        assert result >= 4.0, "Value just below 100 should convert to >= 4.0"
        
        # Test a value that definitely converts to < 5.0 (98.0 / 25 + 1 = 4.92, rounds to 4.9)
        result = CheckinAnalytics.convert_score_100_to_5(98.0)
        assert result < 5.0, "98.0 should convert to < 5.0"
        assert result > 4.0, "98.0 should convert to > 4.0"


class TestScoreConversion5To100:
    """Test conversion from 1-5 scale to 0-100 scale."""
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_0_to_0(self):
        """Test that 0 converts to 0."""
        result = CheckinAnalytics.convert_score_5_to_100(0)
        assert result == 0.0, "0 should convert to 0.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_negative_to_0(self):
        """Test that negative values convert to 0."""
        result = CheckinAnalytics.convert_score_5_to_100(-1)
        assert result == 0.0, "Negative values should convert to 0.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_5_to_100(self):
        """Test that 5 converts to 100."""
        result = CheckinAnalytics.convert_score_5_to_100(5)
        assert result == 100.0, "5 should convert to 100.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_3_to_50(self):
        """Test that 3 converts to 50 (middle value)."""
        result = CheckinAnalytics.convert_score_5_to_100(3)
        assert result == 50.0, "3 should convert to 50.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_1_to_0(self):
        """Test that 1 converts to 0."""
        result = CheckinAnalytics.convert_score_5_to_100(1)
        assert result == 0.0, "1 should convert to 0.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_2_to_25(self):
        """Test that 2 converts to 25."""
        result = CheckinAnalytics.convert_score_5_to_100(2)
        assert result == 25.0, "2 should convert to 25.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_4_to_75(self):
        """Test that 4 converts to 75."""
        result = CheckinAnalytics.convert_score_5_to_100(4)
        assert result == 75.0, "4 should convert to 75.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_decimal_values(self):
        """Test that decimal values convert correctly."""
        # 2.5 should convert to 37.5 ((2.5 - 1) * 25 = 37.5)
        result = CheckinAnalytics.convert_score_5_to_100(2.5)
        assert result == 37.5, "2.5 should convert to 37.5"
        
        # 3.5 should convert to 62.5 ((3.5 - 1) * 25 = 62.5)
        result = CheckinAnalytics.convert_score_5_to_100(3.5)
        assert result == 62.5, "3.5 should convert to 62.5"
        
        # Test various non-integer values users might report
        # Note: Using approximate equality due to floating point precision
        test_cases = [
            (1.1, 2.5),   # Just above 1: (1.1 - 1) * 25 = 2.5
            (2.3, 32.5),  # Between 2 and 3: (2.3 - 1) * 25 = 32.5
            (3.7, 67.5),  # Between 3 and 4: (3.7 - 1) * 25 = 67.5
            (4.9, 97.5),  # Just below 5: (4.9 - 1) * 25 = 97.5
            (1.5, 12.5),  # Halfway between 1 and 2: (1.5 - 1) * 25 = 12.5
            (4.2, 80.0),  # Between 4 and 5: (4.2 - 1) * 25 = 80.0
        ]
        
        for score_5, expected_100 in test_cases:
            result = CheckinAnalytics.convert_score_5_to_100(score_5)
            # Use approximate equality to handle floating point precision
            assert abs(result - expected_100) < 0.01, f"{score_5} should convert to ~{expected_100}, got {result}"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_convert_edge_cases(self):
        """Test edge case values."""
        # Test values just above 1
        result = CheckinAnalytics.convert_score_5_to_100(1.1)
        assert result > 0, "Value just above 1 should convert to > 0"
        
        # Test values just below 5
        result = CheckinAnalytics.convert_score_5_to_100(4.9)
        assert result < 100.0, "Value just below 5 should convert to < 100.0"
        assert result > 90.0, "Value just below 5 should convert to > 90.0"


class TestScoreConversionRoundTrip:
    """Test that conversions are reversible (round-trip)."""
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_round_trip_1_to_5(self):
        """Test round-trip conversion for all integer values 1-5."""
        # Note: 1 converts to 0, which converts back to 0 (not 1), so we skip 1
        for score_5 in [2, 3, 4, 5]:
            score_100 = CheckinAnalytics.convert_score_5_to_100(score_5)
            result_5 = CheckinAnalytics.convert_score_100_to_5(score_100)
            assert abs(result_5 - score_5) < 0.1, f"Round-trip for {score_5} should be close to original"
        
        # Test 1 separately - it converts to 0, which is expected behavior
        score_100 = CheckinAnalytics.convert_score_5_to_100(1)
        assert score_100 == 0.0, "1 should convert to 0.0"
        result_5 = CheckinAnalytics.convert_score_100_to_5(0.0)
        assert result_5 == 0.0, "0.0 should convert back to 0.0"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_round_trip_0_to_100(self):
        """Test round-trip conversion for key 0-100 values."""
        test_values = [0, 25, 50, 75, 100]
        for score_100 in test_values:
            if score_100 == 0:
                # 0 converts to 0, which converts back to 0
                continue
            score_5 = CheckinAnalytics.convert_score_100_to_5(score_100)
            result_100 = CheckinAnalytics.convert_score_5_to_100(score_5)
            # Allow small rounding differences
            assert abs(result_100 - score_100) < 1.0, f"Round-trip for {score_100} should be close to original"
    
    @pytest.mark.unit
    @pytest.mark.analytics
    def test_round_trip_decimal_values(self):
        """Test round-trip conversion for decimal values."""
        test_values = [1.5, 2.5, 3.5, 4.5]
        for score_5 in test_values:
            score_100 = CheckinAnalytics.convert_score_5_to_100(score_5)
            result_5 = CheckinAnalytics.convert_score_100_to_5(score_100)
            # Allow small rounding differences due to rounding to 1 decimal
            assert abs(result_5 - score_5) < 0.2, f"Round-trip for {score_5} should be close to original"

