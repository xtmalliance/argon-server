from django.utils.translation import gettext_lazy as _

OPERATION_STATES = ((0, _('Not Submitted')),(1, _('Accepted')),(2, _('Activated')),(3,_('Nonconforming')),(4,_('Contingent')),(5,_('Ended')),)
OPERATION_TYPES = ((1, _('VLOS')),(2, _('BVLOS')),(3,_('CREWED')),)        
    