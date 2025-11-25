"""Tests for CLI."""

from src.cli.main import main, create_parser


class TestCLI:
    """Tests for CLI functionality."""

    def test_parser_creation(self):
        """Test that parser is created correctly."""
        parser = create_parser()
        assert parser is not None

    def test_no_command_shows_help(self):
        """Test that no command shows help."""
        result = main([])
        assert result == 0

    def test_info_command(self):
        """Test info command."""
        result = main(["info"])
        assert result == 0

    def test_generate_command(self):
        """Test generate command."""
        result = main(["generate", "nfl"])
        assert result == 0

    def test_generate_with_options(self):
        """Test generate command with options."""
        result = main(["generate", "nfl", "--legs", "3", "--stake", "20"])
        assert result == 0

    def test_generate_safe_mode(self):
        """Test generate command with safe mode."""
        result = main(["generate", "nfl", "--mode", "safe"])
        assert result == 0

    def test_generate_aggressive_mode(self):
        """Test generate command with aggressive mode."""
        result = main(["generate", "nfl", "--mode", "aggressive"])
        assert result == 0

    def test_matchups_command(self):
        """Test matchups command."""
        result = main(["matchups", "nfl"])
        assert result == 0

    def test_analyze_command(self):
        """Test analyze command."""
        result = main(["analyze", "nfl", "KC", "SF"])
        assert result == 0

    def test_analyze_verbose(self):
        """Test analyze command with verbose flag."""
        result = main(["analyze", "nfl", "KC", "SF", "--verbose"])
        assert result == 0
