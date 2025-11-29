"""Long-term memory storage using JSON files."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..models import RepositoryProfile, UserPreferences, MaintenanceSuggestion


class MemoryBank:
    """Manages long-term storage of repository profiles, user preferences, and suggestions."""
    
    def __init__(self, storage_dir: str = ".github_maintainer_memory"):
        """
        Initialize the memory bank with a storage directory.
        
        Args:
            storage_dir: Directory path for storing memory files
        """
        self.storage_dir = Path(storage_dir)
        self._ensure_storage_structure()
    
    def _ensure_storage_structure(self) -> None:
        """Create storage directory structure if it doesn't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "profiles").mkdir(exist_ok=True)
        (self.storage_dir / "preferences").mkdir(exist_ok=True)
        (self.storage_dir / "suggestions").mkdir(exist_ok=True)
    
    def _get_profile_path(self, repo_full_name: str) -> Path:
        """Get the file path for a repository profile."""
        # Replace / with _ to create valid filename
        safe_name = repo_full_name.replace("/", "_")
        return self.storage_dir / "profiles" / f"{safe_name}.json"
    
    def _get_preferences_path(self, user_id: str) -> Path:
        """Get the file path for user preferences."""
        return self.storage_dir / "preferences" / f"{user_id}.json"
    
    def _get_suggestions_path(self, repo_full_name: str) -> Path:
        """Get the file path for repository suggestions."""
        safe_name = repo_full_name.replace("/", "_")
        return self.storage_dir / "suggestions" / f"{safe_name}.json"
    
    # Repository Profile Methods
    
    def save_repository_profile(self, profile: RepositoryProfile) -> None:
        """
        Save a repository profile to long-term storage.
        
        Args:
            profile: The repository profile to save
            
        Raises:
            ValueError: If profile validation fails
        """
        profile.validate()
        
        profile_path = self._get_profile_path(profile.repository.full_name)
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    def load_repository_profile(self, repo_full_name: str) -> Optional[RepositoryProfile]:
        """
        Load a repository profile from long-term storage.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            
        Returns:
            RepositoryProfile if found, None otherwise
        """
        profile_path = self._get_profile_path(repo_full_name)
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return RepositoryProfile.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Log error but don't crash - return None for corrupted data
            print(f"Warning: Failed to load profile for {repo_full_name}: {e}")
            return None
    
    def delete_repository_profile(self, repo_full_name: str) -> bool:
        """
        Delete a repository profile from storage.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            
        Returns:
            True if profile was deleted, False if not found
        """
        profile_path = self._get_profile_path(repo_full_name)
        
        if profile_path.exists():
            profile_path.unlink()
            return True
        return False
    
    def list_repository_profiles(self) -> List[str]:
        """
        List all stored repository profiles.
        
        Returns:
            List of repository full names
        """
        profiles_dir = self.storage_dir / "profiles"
        if not profiles_dir.exists():
            return []
        
        profiles = []
        for file_path in profiles_dir.glob("*.json"):
            # Convert filename back to repo full name
            repo_name = file_path.stem.replace("_", "/")
            profiles.append(repo_name)
        
        return profiles
    
    # User Preferences Methods
    
    def save_user_preferences(self, preferences: UserPreferences) -> None:
        """
        Save user preferences to long-term storage.
        
        Args:
            preferences: The user preferences to save
            
        Raises:
            ValueError: If preferences validation fails
        """
        preferences.validate()
        
        prefs_path = self._get_preferences_path(preferences.user_id)
        
        with open(prefs_path, 'w', encoding='utf-8') as f:
            json.dump(preferences.to_dict(), f, indent=2)
    
    def load_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """
        Load user preferences from long-term storage.
        
        Args:
            user_id: The user ID to load preferences for
            
        Returns:
            UserPreferences if found, None otherwise
        """
        prefs_path = self._get_preferences_path(user_id)
        
        if not prefs_path.exists():
            return None
        
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return UserPreferences.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Failed to load preferences for {user_id}: {e}")
            return None
    
    def delete_user_preferences(self, user_id: str) -> bool:
        """
        Delete user preferences from storage.
        
        Args:
            user_id: The user ID to delete preferences for
            
        Returns:
            True if preferences were deleted, False if not found
        """
        prefs_path = self._get_preferences_path(user_id)
        
        if prefs_path.exists():
            prefs_path.unlink()
            return True
        return False
    
    # Suggestion History Methods
    
    def save_suggestions(self, repo_full_name: str, suggestions: List[MaintenanceSuggestion]) -> None:
        """
        Save maintenance suggestions for a repository.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            suggestions: List of maintenance suggestions to save
        """
        for suggestion in suggestions:
            suggestion.validate()
        
        suggestions_path = self._get_suggestions_path(repo_full_name)
        
        # Load existing suggestions if any
        existing_suggestions = self.load_suggestions(repo_full_name)
        
        # Combine with new suggestions
        all_suggestions = existing_suggestions + suggestions
        
        # Serialize all suggestions
        suggestions_data = [s.to_dict() for s in all_suggestions]
        
        with open(suggestions_path, 'w', encoding='utf-8') as f:
            json.dump(suggestions_data, f, indent=2)
    
    def load_suggestions(self, repo_full_name: str) -> List[MaintenanceSuggestion]:
        """
        Load maintenance suggestions for a repository.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            
        Returns:
            List of MaintenanceSuggestion objects (empty list if none found)
        """
        suggestions_path = self._get_suggestions_path(repo_full_name)
        
        if not suggestions_path.exists():
            return []
        
        try:
            with open(suggestions_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [MaintenanceSuggestion.from_dict(s) for s in data]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Failed to load suggestions for {repo_full_name}: {e}")
            return []
    
    def check_suggestion_exists(self, repo_full_name: str, suggestion_title: str) -> bool:
        """
        Check if a suggestion with the given title already exists for a repository.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            suggestion_title: Title of the suggestion to check
            
        Returns:
            True if a suggestion with this title exists, False otherwise
        """
        existing_suggestions = self.load_suggestions(repo_full_name)
        
        for suggestion in existing_suggestions:
            if suggestion.title.lower() == suggestion_title.lower():
                return True
        
        return False
    
    def delete_suggestions(self, repo_full_name: str) -> bool:
        """
        Delete all suggestions for a repository.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            
        Returns:
            True if suggestions were deleted, False if not found
        """
        suggestions_path = self._get_suggestions_path(repo_full_name)
        
        if suggestions_path.exists():
            suggestions_path.unlink()
            return True
        return False
    
    def clear_all_data(self) -> None:
        """Clear all data from memory bank (use with caution)."""
        import shutil
        if self.storage_dir.exists():
            shutil.rmtree(self.storage_dir)
        self._ensure_storage_structure()
