class WaterProfileError(RuntimeError):
    """Base error shown safely to API and UI consumers."""


class ReportDiscoveryError(WaterProfileError):
    """The latest report link could not be discovered."""


class ReportDownloadError(WaterProfileError):
    """The selected report PDF could not be downloaded."""


class ReportParseError(WaterProfileError):
    """The report PDF did not contain the expected mineral values."""


class ReportNotFoundError(WaterProfileError):
    """The requested linked monthly report does not exist."""
