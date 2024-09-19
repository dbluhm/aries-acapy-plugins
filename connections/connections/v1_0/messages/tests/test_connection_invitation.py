from unittest import TestCase, mock

from aries_cloudagent.messaging.models.base import BaseModelError
from aries_cloudagent.protocols.didcomm_prefix import DIDCommPrefix
from ...message_types import CONNECTION_INVITATION
from ..connection_invitation import ConnectionInvitation


class TestConnectionInvitation(TestCase):
    label = "Label"
    did = "did:sov:QmWbsNYhMrjHiqZDTUTEJs"
    endpoint_url = "https://example.com/endpoint"
    endpoint_did = "did:sov:A2wBhNYhMrjHiqZDTUYH7u"
    image_url = "https://example.com/image.jpg"
    key = "8HH5gYEeNc3z7PYXmd54d4x6qAfCNrqQqEB3nS7Zfu7K"

    def test_init(self):
        connection_invitation = ConnectionInvitation(
            label=self.label, recipient_keys=[self.key], endpoint=self.endpoint_url
        )
        assert connection_invitation.label == self.label
        assert connection_invitation.recipient_keys == [self.key]
        assert connection_invitation.endpoint == self.endpoint_url

        connection_invitation = ConnectionInvitation(label=self.label, did=self.did)
        assert connection_invitation.did == self.did

    def test_type(self):
        connection_invitation = ConnectionInvitation(
            label=self.label, recipient_keys=[self.key], endpoint=self.endpoint_url
        )

        assert connection_invitation._type == DIDCommPrefix.qualify_current(
            CONNECTION_INVITATION
        )

    def test_url_round_trip(self):
        connection_invitation = ConnectionInvitation(
            label=self.label, recipient_keys=[self.key], endpoint=self.endpoint_url
        )
        url = connection_invitation.to_url()
        assert isinstance(url, str)
        invitation = ConnectionInvitation.from_url(url)
        assert isinstance(invitation, ConnectionInvitation)

    def test_from_no_url(self):
        url = "http://aries.ca/no_ci"
        assert ConnectionInvitation.from_url(url) is None


class TestConnectionInvitationSchema(TestCase):
    connection_invitation = ConnectionInvitation(
        label="label", did="did:sov:QmWbsNYhMrjHiqZDTUTEJs"
    )

    def test_make_model(self):
        data = self.connection_invitation.serialize()
        model_instance = ConnectionInvitation.deserialize(data)
        assert isinstance(model_instance, ConnectionInvitation)

    def test_make_model_invalid(self):
        x_conns = [
            ConnectionInvitation(
                label="did-and-recip-keys",
                did="did:sov:QmWbsNYhMrjHiqZDTUTEJs",
                recipient_keys=["8HH5gYEeNc3z7PYXmd54d4x6qAfCNrqQqEB3nS7Zfu7K"],
            ),
            ConnectionInvitation(
                label="did-and-endpoint",
                did="did:sov:QmWbsNYhMrjHiqZDTUTEJs",
                endpoint="https://example.com/endpoint",
            ),
            ConnectionInvitation(
                label="no-did-no-recip-keys",
                endpoint="https://example.com/endpoint",
            ),
            ConnectionInvitation(
                label="no-did-no-endpoint",
                recipient_keys=["8HH5gYEeNc3z7PYXmd54d4x6qAfCNrqQqEB3nS7Zfu7K"],
            ),
        ]
        for x_conn in x_conns:
            data = x_conn.serialize()
            with self.assertRaises(BaseModelError):
                ConnectionInvitation.deserialize(data)