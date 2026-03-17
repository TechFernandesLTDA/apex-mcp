"""Tests for apex_mcp.templates — template IDs and constants.

Run: pytest tests/test_templates.py -v
"""
from __future__ import annotations


class TestPageTemplates:
    def test_standard_template_is_large_int(self):
        from apex_mcp.templates import PAGE_TMPL_STANDARD

        assert isinstance(PAGE_TMPL_STANDARD, int)
        assert PAGE_TMPL_STANDARD > 0

    def test_login_template_exists(self):
        from apex_mcp.templates import PAGE_TMPL_LOGIN

        assert PAGE_TMPL_LOGIN is not None
        assert isinstance(PAGE_TMPL_LOGIN, int)

    def test_dialog_and_modal_are_same(self):
        from apex_mcp.templates import PAGE_TMPL_DIALOG, PAGE_TMPL_MODAL

        assert PAGE_TMPL_DIALOG == PAGE_TMPL_MODAL


class TestRegionTemplates:
    def test_standard_region_template(self):
        from apex_mcp.templates import REGION_TMPL_STANDARD

        assert isinstance(REGION_TMPL_STANDARD, int)

    def test_ir_region_template(self):
        from apex_mcp.templates import REGION_TMPL_IR

        assert isinstance(REGION_TMPL_IR, int)

    def test_blank_region_template(self):
        from apex_mcp.templates import REGION_TMPL_BLANK

        assert isinstance(REGION_TMPL_BLANK, int)

    def test_hero_is_none(self):
        from apex_mcp.templates import REGION_TMPL_HERO

        assert REGION_TMPL_HERO is None


class TestButtonTemplates:
    def test_text_and_icon_differ(self):
        from apex_mcp.templates import BTN_TMPL_TEXT, BTN_TMPL_ICON

        assert BTN_TMPL_TEXT != BTN_TMPL_ICON
        assert isinstance(BTN_TMPL_TEXT, int)
        assert isinstance(BTN_TMPL_ICON, int)


class TestItemTypes:
    def test_item_type_constants(self):
        from apex_mcp.templates import (
            ITEM_TEXT, ITEM_NUMBER, ITEM_DATE, ITEM_SELECT,
            ITEM_HIDDEN, ITEM_TEXTAREA, ITEM_YES_NO,
            ITEM_PASSWORD, ITEM_DISPLAY, ITEM_CHECKBOX, ITEM_RADIO,
        )

        all_types = [ITEM_TEXT, ITEM_NUMBER, ITEM_DATE, ITEM_SELECT,
                     ITEM_HIDDEN, ITEM_TEXTAREA, ITEM_YES_NO,
                     ITEM_PASSWORD, ITEM_DISPLAY, ITEM_CHECKBOX, ITEM_RADIO]
        for t in all_types:
            assert t.startswith("NATIVE_")
        assert len(set(all_types)) == len(all_types), "All item types must be unique"


class TestRegionTypes:
    def test_region_type_constants(self):
        from apex_mcp.templates import REGION_IR, REGION_FORM, REGION_STATIC, REGION_PLSQL, REGION_CHART

        for rt in (REGION_IR, REGION_FORM, REGION_STATIC, REGION_PLSQL, REGION_CHART):
            assert rt.startswith("NATIVE_")


class TestButtonActions:
    def test_action_constants(self):
        from apex_mcp.templates import BTN_ACTION_SUBMIT, BTN_ACTION_REDIRECT, BTN_ACTION_DEFINED

        assert BTN_ACTION_SUBMIT == "SUBMIT"
        assert BTN_ACTION_REDIRECT == "REDIRECT_URL"
        assert BTN_ACTION_DEFINED == "DEFINED_BY_DA"


class TestProcessTypes:
    def test_proc_types(self):
        from apex_mcp.templates import PROC_DML, PROC_PLSQL

        assert PROC_DML == "NATIVE_FORM_DML"
        assert PROC_PLSQL == "NATIVE_PLSQL"


class TestDynamicActionEvents:
    def test_da_events(self):
        from apex_mcp.templates import DA_CLICK, DA_CHANGE, DA_LOAD

        assert DA_CLICK == "click"
        assert DA_CHANGE == "change"
        assert DA_LOAD == "page-load"


class TestChecksumSalt:
    def test_checksum_salt_is_long_string(self):
        from apex_mcp.templates import CHECKSUM_SALT

        assert isinstance(CHECKSUM_SALT, str)
        assert len(CHECKSUM_SALT) >= 32
