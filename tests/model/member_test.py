import unittest
from myemma.adapter import AbstractAdapter
from myemma.model import NoMemberEmailError, NoMemberIdError, NoMemberStatusError
from myemma.model.account import Account
from myemma.model.member import (Member, MemberGroupCollection,
                                 MemberMailingCollection  )
from myemma.model.group import Group
from myemma.model.mailing import Mailing


class MockAdapter(AbstractAdapter):
    expected = None

    def __init__(self, *args, **kwargs):
        self.called = 0
        self.call = ()

    def _capture(self, method, path, params):
        self.called += 1
        self.call = (method, path, params)

    def get(self, path, params={}):
        self._capture('GET', path, params)
        return self.__class__.expected

    def post(self, path, data={}):
        self._capture('POST', path, data)
        return self.__class__.expected

    def put(self, path, params={}):
        self._capture('PUT', path, params)
        return self.__class__.expected

    def delete(self, path, params={}):
        self._capture('DELETE', path, params)
        return self.__class__.expected


class MemberTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.member = Member(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"opt-out"
            }
        )
        self.member.account.fields._dict = {
            2000: {'shortcut_name': u"first_name"},
            2001: {'shortcut_name': u"last_name"}
        }

    def test_can_set_valid_field_value_with_dictionary_access(self):
        self.member['first_name'] = u"Emma"
        self.assertEquals(u"Emma", self.member['first_name'])

    def test_group_collection_can_be_accessed(self):
        self.assertIsInstance(self.member.groups, MemberGroupCollection)

    def test_mailing_collection_can_be_accessed(self):
        self.assertIsInstance(self.member.mailings, MemberMailingCollection)

    def test_can_get_opt_out_detail_for_member(self):
        MockAdapter.expected = []
        detail = self.member.get_opt_out_detail()
        self.assertIsInstance(detail, list)
        self.assertEquals(self.member.account.adapter.called, 1)
        self.assertEquals(
            self.member.account.adapter.call,
            ('GET', '/members/1000/optout', {}))

    def test_can_get_opt_out_detail_for_member2(self):
        MockAdapter.expected = []
        member = Member(self.member.account)
        with self.assertRaises(NoMemberIdError):
            member.get_opt_out_detail()
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_ask_if_member_has_opted_out(self):
        has_opted_out = self.member.has_opted_out()
        self.assertIsInstance(has_opted_out, bool)
        self.assertTrue(has_opted_out)
        self.assertEquals(self.member.account.adapter.called, 0)

    def test_can_ask_if_member_has_opted_out2(self):
        member = Member(
            self.member.account,
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"active"
            }
        )
        has_opted_out = member.has_opted_out()
        self.assertIsInstance(has_opted_out, bool)
        self.assertFalse(has_opted_out)
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_ask_if_member_has_opted_out3(self):
        member = Member(self.member.account)
        with self.assertRaises(NoMemberStatusError):
            member.has_opted_out()
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_opt_out_a_member(self):
        member = Member(self.member.account)
        with self.assertRaises(NoMemberEmailError):
            member.opt_out()
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_opt_out_a_member2(self):
        member = Member(
            self.member.account,
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"active"
            }
        )
        MockAdapter.expected = True
        self.assertFalse(member.has_opted_out())
        result = member.opt_out()
        self.assertIsNone(result)
        self.assertEquals(member.account.adapter.called, 1)
        self.assertEquals(
            member.account.adapter.call,
            ('PUT', '/members/email/optout/test@example.com', {}))
        self.assertTrue(member.has_opted_out())

    def test_can_save_a_member(self):
        mbr = Member(self.member.account, {'email':u"test@example.com"})
        MockAdapter.expected = {
            'status': u"a",
            'added': True,
            'member_id': 1024
        }
        result = mbr.save()
        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(
            mbr.account.adapter.call,
            ('POST', '/members/add', {'email':u"test@example.com"}))
        self.assertEquals(1024, mbr['member_id'])
        self.assertEquals(u"a", mbr['status_code'])

    def test_can_save_a_member2(self):
        mbr = Member(
            self.member.account,
            {'email':u"test@example.com",
             'first_name':u"Emma"})
        MockAdapter.expected = {
            'status': u"a",
            'added': True,
            'member_id': 1024
        }
        result = mbr.save()
        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(
            mbr.account.adapter.call,
            ('POST', '/members/add', {'email':u"test@example.com",
                                      'fields': {'first_name': u"Emma"}}))
        self.assertEquals(1024, mbr['member_id'])
        self.assertEquals(u"a", mbr['status_code'])

    def test_can_save_a_member3(self):
        mbr = Member(
            self.member.account,
            {'email':u"test@example.com",
             'first_name':u"Emma"})
        MockAdapter.expected = {
            'status': u"a",
            'added': True,
            'member_id': 1024
        }
        result = mbr.save(signup_form_id=u"http://example.com/signup")
        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(
            mbr.account.adapter.call,
            ('POST', '/members/add', {
                'email':u"test@example.com",
                'fields': {'first_name': u"Emma"},
                'signup_form_id': u"http://example.com/signup"}
            ))
        self.assertEquals(1024, mbr['member_id'])
        self.assertEquals(u"a", mbr['status_code'])


class MemberGroupCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.groups =  Member(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"opt-out"
            }
        ).groups

    def test_fetch_all_returns_a_dictionary(self):
        groups = MemberGroupCollection(Member(self.groups.member.account))
        with self.assertRaises(NoMemberIdError):
            groups.fetch_all()
        self.assertEquals(groups.member.account.adapter.called, 0)

    def test_fetch_all_returns_a_dictionary2(self):
        MockAdapter.expected = [{'group_name': u"Test Group"}]
        self.assertIsInstance(self.groups.fetch_all(), dict)
        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            ('GET', '/members/1000/groups', {}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'group_name': u"Test Group"}]
        self.assertEquals(0, len(self.groups))
        self.groups.fetch_all()
        self.assertEquals(1, len(self.groups))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'group_name': u"Test Group"}]
        self.groups.fetch_all()
        self.groups.fetch_all()
        self.assertEquals(self.groups.member.account.adapter.called, 1)

    def test_collection_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'group_name': u"Test Group"}]
        self.groups.fetch_all()
        self.assertIsInstance(self.groups, MemberGroupCollection)
        self.assertEquals(1, len(self.groups))
        self.assertIsInstance(self.groups[u"Test Group"], Group)


class MemberMailingCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.mailings =  Member(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"opt-out"
            }
        ).mailings

    def test_fetch_all_returns_a_dictionary(self):
        member = Member(self.mailings.member.account)
        mailings = MemberMailingCollection(member)
        with self.assertRaises(NoMemberIdError):
            mailings.fetch_all()
        self.assertEquals(mailings.member.account.adapter.called, 0)

    def test_fetch_all_returns_a_dictionary2(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.assertIsInstance(self.mailings.fetch_all(), dict)
        self.assertEquals(self.mailings.member.account.adapter.called, 1)
        self.assertEquals(
            self.mailings.member.account.adapter.call,
            ('GET', '/members/1000/mailings', {}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.assertEquals(0, len(self.mailings))
        self.mailings.fetch_all()
        self.assertEquals(1, len(self.mailings))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.mailings.fetch_all()
        self.mailings.fetch_all()
        self.assertEquals(self.mailings.member.account.adapter.called, 1)

    def test_collection_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.mailings.fetch_all()
        self.assertIsInstance(self.mailings, MemberMailingCollection)
        self.assertEquals(1, len(self.mailings))
        self.assertIsInstance(self.mailings[201], Mailing)