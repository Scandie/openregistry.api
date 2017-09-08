# -*- coding: utf-8 -*-
from mock import MagicMock, Mock
from functools import partial
from cornice.resource import resource

from openregistry.api.utils import (
	error_handler, get_now, generate_id,
	json_view, set_ownership,
    context_unpack, APIResourceListing
)

VIEW_MAP = {
    u'': MagicMock(),
    u'test': MagicMock()
}
CHANGES_VIEW_MAP = {
    u'': MagicMock(),
    u'test': MagicMock()
}
FEED = {
    u'changes': CHANGES_VIEW_MAP,
    u'dateModified': VIEW_MAP
}
FIELDS = MagicMock()
dummy_resource_serialize = Mock()

opdummyresource = partial(resource,
                           error_handler=error_handler)

@opdummyresource(name='DummyResources',
                  path='/dummy_resources',
                  description="Open Contracting compatible data exchange format.")
class DummyResource(APIResourceListing):

    def __init__(self, request, context):
        super(DummyResource, self).__init__(request, context)
        # params for listing
        self.VIEW_MAP = VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = dummy_resource_serialize
        self.object_name_for_listing = 'DummyResources'
        self.log_message_id = 'dummy_resource_list_custom'
