"""
Data models for GitHub Profile README Generator

This module contains all data classes used to structure the scraped GitHub data.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class UserProfile:
    """Data class to store GitHub user profile information."""
    name: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    website: Optional[str]
    twitter: Optional[str]
    location: Optional[str]
    email: Optional[str]
    public_repos: int
    followers: int
    following: int
    profile_readme: Optional[str]
    avatar_url: Optional[str]
    login: str


@dataclass
class Repository:
    """Data class to store GitHub repository information."""
    name: str
    about: Optional[str]
    description: Optional[str]
    readme_content: Optional[str]
    languages: Dict[str, int]
    url: str
    stars: int
    forks: int
    is_fork: bool
    default_branch: str


@dataclass
class ScrapingStatistics:
    """Data class to store scraping statistics."""
    total_repositories: int
    repositories_with_readme: int
    total_stars: int
    total_forks: int
    unique_languages: List[str]
    language_distribution: Dict[str, int]


@dataclass
class ScrapingMetadata:
    """Data class to store scraping metadata."""
    scraped_at: str
    scraper_version: str
    total_api_requests: int
    saved_to_file: Optional[str] = None
    save_error: Optional[str] = None


@dataclass
class CompleteUserData:
    """Data class to store complete user scraping results."""
    profile: UserProfile
    repositories: List[Repository]
    statistics: ScrapingStatistics
    metadata: ScrapingMetadata