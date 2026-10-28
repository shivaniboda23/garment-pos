"""Regression checks for public staging access and the one-time bootstrap."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes import auth
from app.crud import auth as auth_crud
from app import dependencies
from scripts.bootstrap_staging_shop import _validate_target


class FakeDatabase:
    def __init__(self, user=None):
        self.user = user
        self.lookups = 0

    def get(self, model, user_id):
        self.lookups += 1
        return self.user

    def scalar(self, statement):
        return self.user


class PublicStagingGuardTests(unittest.TestCase):
    def test_registration_is_closed_by_default(self):
        with patch.object(auth, "PUBLIC_REGISTRATION_ENABLED", False), patch.object(
            auth, "register_shop"
        ) as create:
            with self.assertRaises(HTTPException) as error:
                auth.register(SimpleNamespace(), FakeDatabase())
        self.assertEqual(404, error.exception.status_code)
        create.assert_not_called()

    def test_registration_preserves_duplicate_message_when_enabled(self):
        with patch.object(auth, "PUBLIC_REGISTRATION_ENABLED", True), patch.object(
            auth, "register_shop", side_effect=auth_crud.DuplicateEmailError()
        ):
            with self.assertRaises(HTTPException) as error:
                auth.register(SimpleNamespace(), FakeDatabase())
        self.assertEqual(400, error.exception.status_code)
        self.assertEqual("Email already registered", error.exception.detail)

    def test_registration_creates_shop_when_explicitly_enabled(self):
        shop = SimpleNamespace(id=7, shop_name="Demo")
        request = SimpleNamespace()
        db = FakeDatabase()
        with patch.object(auth, "PUBLIC_REGISTRATION_ENABLED", True), patch.object(
            auth, "register_shop", return_value=shop
        ) as create:
            result = auth.register(request, db)
        create.assert_called_once_with(db, request)
        self.assertEqual(7, result["shop_id"])

    def test_registration_hides_unexpected_database_errors(self):
        with patch.object(auth, "PUBLIC_REGISTRATION_ENABLED", True), patch.object(
            auth, "register_shop", side_effect=RuntimeError("private database detail")
        ):
            with self.assertRaises(HTTPException) as error:
                auth.register(SimpleNamespace(), FakeDatabase())
        self.assertEqual(500, error.exception.status_code)
        self.assertNotIn("private database detail", error.exception.detail)

    def test_inactive_user_cannot_log_in(self):
        user = SimpleNamespace(is_active=False, password="stored hash")
        with patch.object(auth_crud, "verify_password") as verify:
            self.assertIsNone(
                auth_crud.authenticate_user(FakeDatabase(user), "test@example.com", "pw")
            )
        verify.assert_not_called()

    def test_active_user_password_check_is_preserved(self):
        user = SimpleNamespace(is_active=True, password="stored hash")
        with patch.object(auth_crud, "verify_password", return_value=True) as verify:
            self.assertIs(user, auth_crud.authenticate_user(
                FakeDatabase(user), "test@example.com", "pw"
            ))
        verify.assert_called_once_with("pw", "stored hash")

    def test_rejected_token_claims_never_fetch_a_user(self):
        for claims in (None, {}, {"user_id": "1", "shop_id": 3},
                       {"user_id": True, "shop_id": 3}):
            with self.subTest(claims=claims), patch.object(
                dependencies, "verify_access_token", return_value=claims
            ):
                db = FakeDatabase()
                with self.assertRaises(HTTPException) as error:
                    dependencies.get_current_user("token", db)
                self.assertEqual(401, error.exception.status_code)
                self.assertEqual(0, db.lookups)

    def test_inactive_or_different_shop_user_is_rejected(self):
        claims = {"user_id": 5, "shop_id": 3}
        for user in (SimpleNamespace(is_active=False, shop_id=3),
                     SimpleNamespace(is_active=True, shop_id=4)):
            with self.subTest(user=user), patch.object(
                dependencies, "verify_access_token", return_value=claims
            ):
                with self.assertRaises(HTTPException) as error:
                    dependencies.get_current_user("token", FakeDatabase(user))
                self.assertEqual(401, error.exception.status_code)

    def test_valid_active_user_is_returned(self):
        user = SimpleNamespace(is_active=True, shop_id=3)
        with patch.object(dependencies, "verify_access_token", return_value={
            "user_id": 5, "shop_id": 3
        }):
            self.assertIs(user, dependencies.get_current_user("token", FakeDatabase(user)))

    def test_bootstrap_requires_fresh_staging_schema_and_matching_name(self):
        _validate_target("bhavani_staging_demo", "c8f0a2d4e6b1", 0, 0,
                         "bhavani_staging_demo")
        for actual, revision, shops, users, expected in (
            ("bhavani_erp_v2", "c8f0a2d4e6b1", 0, 0, "bhavani_erp_v2"),
            ("bhavani_staging_wrong", "c8f0a2d4e6b1", 0, 0, "bhavani_staging_demo"),
            ("bhavani_staging_demo", "b1c27a4e6f0", 0, 0, "bhavani_staging_demo"),
            ("bhavani_staging_demo", "c8f0a2d4e6b1", 1, 0, "bhavani_staging_demo"),
            ("bhavani_staging_demo", "c8f0a2d4e6b1", 0, 1, "bhavani_staging_demo"),
        ):
            with self.subTest(actual=actual, revision=revision, shops=shops, users=users):
                with self.assertRaises(ValueError):
                    _validate_target(actual, revision, shops, users, expected)


if __name__ == "__main__":
    unittest.main()
