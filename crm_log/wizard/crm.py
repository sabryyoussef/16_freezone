
from odoo import api, fields, models

class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def _action_merge(self):
        to_merge = self.duplicated_lead_ids
        result_opportunity = to_merge.merge_opportunity(auto_unlink=False)
        result_opportunity.action_unarchive()

        if result_opportunity.type == "lead":
            self._convert_and_allocate(result_opportunity, [self.user_id.id], team_id=self.team_id.id)
        else:
            if not result_opportunity.user_id or self.force_assignment:
                result_opportunity.write({
                    'user_id': self.user_id.id,
                    'team_id': self.team_id.id,
                    'service': self.lead_id.service,
                    'nationality_id': self.lead_id.nationality_id.id,
                })
        (to_merge - result_opportunity).sudo().unlink()
        return result_opportunity
