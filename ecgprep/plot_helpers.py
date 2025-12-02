import numpy as np


def get_3by4_format(ecg, leads, n_blocks=4, leads_per_block = 3, long_leads=None):
   n_leads, n_samples = ecg.shape
   samples_per_block = n_samples // n_blocks
   if long_leads is None:
        long_leads = ['DII',]
   long_leads = [leads.index(ll) for ll in long_leads]

   ecg_for_plotting = np.zeros([n_blocks *  leads_per_block + len(long_leads) * n_blocks , samples_per_block], dtype=float)
   my_leads = []
   lead_counter_out = 0
   lead_counter_in = 0
   sample_counter = 0
   for i in range(n_blocks):
       ecg_for_plotting[lead_counter_out:lead_counter_out + leads_per_block, :] = ecg[lead_counter_in:lead_counter_in + leads_per_block, sample_counter:sample_counter + samples_per_block]
       my_leads += leads[i*leads_per_block:(i+1)*leads_per_block]

       lead_counter_out += leads_per_block
       lead_counter_in += leads_per_block

       if len(long_leads) > 0:
           for l in long_leads:
               ecg_for_plotting[lead_counter_out, :] = ecg[l, sample_counter:sample_counter + samples_per_block]
               if i == 0:
                   my_leads.append(f'long {leads[l]}')
               else:
                   my_leads.append('')
               lead_counter_out += 1
       sample_counter += samples_per_block

   return ecg_for_plotting, my_leads