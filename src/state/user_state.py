from typing import Dict, Optional, Set


UserSessionData = Dict[str, Optional[str]]
UserDataStorage = Dict[int, Dict[str, Optional[str]]]
UtmEditingStorage = Dict[int, Dict[str, Optional[str]]]
PendingAuthUsers = Set[int]
PendingPasswordChangeUsers = Set[int]
PendingUserDeletion = Set[int]

# In-memory storages. For now simple dicts are sufficient.
user_data: UserDataStorage = {}
utm_editing_data: UtmEditingStorage = {}
pending_password_users: PendingAuthUsers = set()
pending_password_change_users: PendingPasswordChangeUsers = set()
pending_user_deletion: PendingUserDeletion = set()
