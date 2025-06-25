"""
GitHub Profile and Repository Scraper

This module provides the main scraping functionality for GitHub user profiles
and their repositories.
"""

import requests
import time
from dotenv import load_dotenv
import base64
from typing import Dict, List, Optional
from datetime import datetime
import os
from urllib.parse import urljoin

from src.scraper.models import UserProfile, Repository, ScrapingStatistics, ScrapingMetadata, CompleteUserData
from src.scraper.file_handler import FileHandler
from src.scraper.logging_config import setup_logging, get_logger

# Initialize logging
logger = setup_logging('github_scraper', 'scraper.log')

# Loading environment variables
load_dotenv()


class GitHubScraper:
    """
    A comprehensive GitHub scraper for user profiles and repositories.

    This class handles API calls and data processing to gather complete
    information about GitHub users and their repositories.
    """

    def __init__(self, github_token: Optional[str] = None, save_to_file: bool = True):
        """
        Initialize the GitHub scraper.

        Args:
            github_token (Optional[str]): GitHub personal access token for higher rate limits
            save_to_file (bool): Whether to automatically save results to file
        """
        self.base_api_url = "https://api.github.com"
        self.base_url = "https://github.com"
        self.session = requests.Session()
        self._api_requests_count = 0  # Track API requests for metadata
        self.save_to_file = save_to_file

        # Initialize file handler
        self.file_handler = FileHandler()

        # Set up headers
        self.session.headers.update({
            'User-Agent': 'GitHub-Profile-README-Generator/1.0',
            'Accept': 'application/vnd.github.v3+json'
        })

        # Add authentication if token provided
        if github_token:
            self.session.headers['Authorization'] = f'token {github_token}'
            logger.info("GitHub token provided - higher rate limits available")
        else:
            logger.warning("No GitHub token provided - rate limits may apply")

    def _make_api_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request to GitHub API with error handling and rate limiting.

        Args:
            url (str): API endpoint URL
            params (Optional[Dict]): Query parameters

        Returns:
            Optional[Dict]: JSON response data or None if failed
        """
        try:
            self._api_requests_count += 1  # Track API calls
            response = self.session.get(url, params=params, timeout=10)

            # Log rate limit information
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining:
                logger.debug(f"Rate limit remaining: {remaining}")

            # Handle rate limiting
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                current_time = int(time.time())
                wait_time = max(reset_time - current_time, 60)
                logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return self._make_api_request(url, params)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {str(e)}")
            return None

    def _get_readme_content(self, username: str, repo_name: str, default_branch: str = "main") -> Optional[str]:
        """
        Get README content from a repository.

        Args:
            username (str): GitHub username
            repo_name (str): Repository name
            default_branch (str): Default branch name

        Returns:
            Optional[str]: README content or None if not found
        """
        # Try common README file names
        readme_names = ["README.md", "readme.md", "README.rst", "README.txt", "README"]

        for readme_name in readme_names:
            api_url = f"{self.base_api_url}/repos/{username}/{repo_name}/contents/{readme_name}"
            readme_data = self._make_api_request(api_url)

            if readme_data and readme_data.get('content'):
                try:
                    content = base64.b64decode(readme_data['content']).decode('utf-8')
                    logger.info(f"Found README: {readme_name} in {repo_name} ({len(content)} characters)")
                    return content
                except Exception as e:
                    logger.error(f"Failed to decode README content for {repo_name}: {str(e)}")
                    continue

        logger.debug(f"No README found for repository: {repo_name}")
        return None

    def _get_profile_readme(self, username: str) -> Optional[str]:
        """
        Get the profile README from the special username/username repository.

        Args:
            username (str): GitHub username

        Returns:
            Optional[str]: Profile README content or None if not found
        """
        profile_readme = self._get_readme_content(username, username)
        if profile_readme:
            logger.info(f"Found profile README for user: {username}")
        return profile_readme

    def get_user_profile(self, username: str) -> Optional[UserProfile]:
        """
        Scrape comprehensive user profile information.

        Args:
            username (str): GitHub username to scrape

        Returns:
            Optional[UserProfile]: User profile data or None if failed
        """
        logger.info(f"Fetching profile information for user: {username}")

        # Get user data from API
        api_url = f"{self.base_api_url}/users/{username}"
        user_data = self._make_api_request(api_url)

        if not user_data:
            logger.error(f"Failed to fetch user data for: {username}")
            return None

        # Get profile README
        profile_readme = self._get_profile_readme(username)

        # Extract social media links
        twitter_username = user_data.get('twitter_username')

        profile = UserProfile(
            name=user_data.get('name'),
            bio=user_data.get('bio'),
            company=user_data.get('company'),
            website=user_data.get('blog'),
            twitter=f"https://twitter.com/{twitter_username}" if twitter_username else None,
            location=user_data.get('location'),
            email=user_data.get('email'),
            public_repos=user_data.get('public_repos', 0),
            followers=user_data.get('followers', 0),
            following=user_data.get('following', 0),
            profile_readme=profile_readme,
            avatar_url=user_data.get('avatar_url'),
            login=user_data.get('login', username)
        )

        logger.info(f"Successfully fetched profile for: {username}")
        return profile

    def get_repository_languages(self, username: str, repo_name: str) -> Dict[str, int]:
        """
        Get programming languages used in a repository.

        Args:
            username (str): GitHub username
            repo_name (str): Repository name

        Returns:
            Dict[str, int]: Dictionary of languages and their byte counts
        """
        api_url = f"{self.base_api_url}/repos/{username}/{repo_name}/languages"
        languages_data = self._make_api_request(api_url)

        return languages_data if languages_data else {}

    def get_user_repositories(self, username: str) -> List[Repository]:
        """
        Scrape all repositories for a given user.

        Args:
            username (str): GitHub username to scrape repositories for

        Returns:
            List[Repository]: List of repository data
        """
        logger.info(f"Fetching repositories for user: {username}")

        repositories = []
        page = 1
        per_page = 100

        while True:
            api_url = f"{self.base_api_url}/users/{username}/repos"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'updated',
                'direction': 'desc'
            }

            repos_data = self._make_api_request(api_url, params)

            if not repos_data or len(repos_data) == 0:
                break

            for repo_data in repos_data:
                repo_name = repo_data.get('name', '')
                default_branch = repo_data.get('default_branch', 'main')

                logger.debug(f"Processing repository: {repo_name}")

                # Get README content
                readme_content = self._get_readme_content(username, repo_name, default_branch)

                # Get languages
                languages = self.get_repository_languages(username, repo_name)

                # Add small delay to avoid overwhelming the API
                time.sleep(0.1)

                repository = Repository(
                    name=repo_name,
                    about=repo_data.get('description'),  # GitHub API uses 'description' for what users see as 'About'
                    description=repo_data.get('description'),
                    readme_content=readme_content,
                    languages=languages,
                    url=repo_data.get('html_url', ''),
                    stars=repo_data.get('stargazers_count', 0),
                    forks=repo_data.get('forks_count', 0),
                    is_fork=repo_data.get('fork', False),
                    default_branch=default_branch
                )

                repositories.append(repository)

            # Check if we've got all repositories
            if len(repos_data) < per_page:
                break

            page += 1

        logger.info(f"Successfully fetched {len(repositories)} repositories for: {username}")
        return repositories

    def _calculate_statistics(self, repositories: List[Repository]) -> ScrapingStatistics:
        """
        Calculate statistics from scraped repositories.

        Args:
            repositories (List[Repository]): List of repositories

        Returns:
            ScrapingStatistics: Calculated statistics
        """
        total_stars = sum(repo.stars for repo in repositories)
        total_forks = sum(repo.forks for repo in repositories)
        repos_with_readme = sum(1 for repo in repositories if repo.readme_content)

        # Aggregate language statistics
        all_languages = {}
        for repo in repositories:
            for lang, bytes_count in repo.languages.items():
                all_languages[lang] = all_languages.get(lang, 0) + bytes_count

        return ScrapingStatistics(
            total_repositories=len(repositories),
            repositories_with_readme=repos_with_readme,
            total_stars=total_stars,
            total_forks=total_forks,
            unique_languages=list(all_languages.keys()),
            language_distribution=all_languages
        )

    def scrape_user_complete(self, username: str, save_to_file: Optional[bool] = None) -> CompleteUserData:
        """
        Scrape complete user profile and repository information.

        Args:
            username (str): GitHub username to scrape
            save_to_file (Optional[bool]): Override default save behavior

        Returns:
            CompleteUserData: Complete user data including profile and repositories

        Raises:
            Exception: If scraping fails
        """
        logger.info(f"Starting complete scrape for user: {username}")

        # Get user profile
        profile = self.get_user_profile(username)
        if not profile:
            raise Exception(f"Failed to fetch profile for: {username}")

        # Get user repositories
        repositories = self.get_user_repositories(username)

        # Calculate statistics
        statistics = self._calculate_statistics(repositories)

        # Create metadata
        metadata = ScrapingMetadata(
            scraped_at=datetime.now().isoformat(),
            scraper_version='1.0.0',
            total_api_requests=self._api_requests_count
        )

        # Create complete data object
        complete_data = CompleteUserData(
            profile=profile,
            repositories=repositories,
            statistics=statistics,
            metadata=metadata
        )

        # Save to file if requested
        should_save = save_to_file if save_to_file is not None else self.save_to_file
        if should_save:
            try:
                # Convert to dict for saving
                data_dict = {
                    'profile': profile,
                    'repositories': repositories,
                    'statistics': statistics,
                    'metadata': metadata
                }
                filepath = self.file_handler.save_to_json(data_dict, username)
                complete_data.metadata.saved_to_file = filepath
                logger.info(f"Results saved to: {filepath}")
            except Exception as e:
                logger.error(f"Failed to save results to file: {str(e)}")
                complete_data.metadata.save_error = str(e)

        logger.info(f"Complete scrape finished for: {username}")
        logger.info(f"Summary: {statistics.total_repositories} repos, "
                    f"{statistics.repositories_with_readme} with README, "
                    f"{len(statistics.unique_languages)} languages, "
                    f"{statistics.total_stars} total stars")

        return complete_data


def main():
    """
    Example usage of the GitHub scraper with file output.
    """
    # Initialize scraper (add your GitHub token for higher rate limits)
    scraper = GitHubScraper(github_token=os.getenv("GITHUB_TOKEN"), save_to_file=True)  # Replace None with your token

    # Example: Scrape a user's complete profile and repositories
    username = "Ojjoj"  # Replace with desired username

    try:
        user_data = scraper.scrape_user_complete(username)

        print(f"\n=== Profile Information for {username} ===")
        print(f"Name: {user_data.profile.name}")
        print(f"Bio: {user_data.profile.bio}")
        print(f"Company: {user_data.profile.company}")
        print(f"Website: {user_data.profile.website}")
        print(f"Location: {user_data.profile.location}")
        print(f"Public Repos: {user_data.profile.public_repos}")
        print(f"Followers: {user_data.profile.followers}")
        print(f"Profile README: {'Yes' if user_data.profile.profile_readme else 'No'}")

        print(f"\n=== Repository Statistics ===")
        print(f"Total repositories scraped: {user_data.statistics.total_repositories}")
        print(f"Repositories with README: {user_data.statistics.repositories_with_readme}")
        print(f"Total stars: {user_data.statistics.total_stars}")
        print(f"Total forks: {user_data.statistics.total_forks}")
        print(f"Languages used: {', '.join(user_data.statistics.unique_languages[:5])}")

        print(f"\n=== Sample Repositories (First 3) ===")
        for repo in user_data.repositories[:3]:  # Show first 3 repos
            print(f"\nRepository: {repo.name}")
            print(f"  Description: {repo.description}")
            print(f"  Stars: {repo.stars}")
            print(f"  Languages: {list(repo.languages.keys())}")
            print(f"  README length: {len(repo.readme_content) if repo.readme_content else 0} characters")

        # Show file save information
        if user_data.metadata.saved_to_file:
            print(f"\n=== Output File ===")
            print(f"Data saved to: {user_data.metadata.saved_to_file}")

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        print(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    main()