from __future__ import print_function
from __future__ import division
from . import C_

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import flamingchoripan.cuteplots.plots as cplots

###################################################################################################################################################

def plot_obse_samplers(lcdataset, set_name, obse_sampler_bdict,
	original_space:bool=1,
	pdf_scale:float=0.01,
	figsize:tuple=(12,8),
	add_samples=0,
	):
	fig, axs = plt.subplots(1, 2, figsize=figsize)
	band_names = obse_sampler_bdict.keys()
	lcset = lcdataset[set_name]
	for kb,b in enumerate(band_names):
		ax = axs[kb]
		obse_sampler = obse_sampler_bdict[b]
		if original_space:
			label = '$p(x_{ij},\sigma_{xij})$'+f' {set_name} samples'
			ax.plot(obse_sampler.raw_obse, obse_sampler.raw_obs, 'k.', markersize=2, alpha=0.2); ax.plot(np.nan, np.nan, 'k.', label=label)

			### add samples
			if add_samples:
				n = int(2e3)
				to_sample = obse_sampler.raw_obs
				std = 1e-4
				new_obs = [np.random.normal(to_sample[np.random.randint(0, len(to_sample))], std) for _ in range(n)] # kde
				#x = 0.05; new_obs = np.linspace(x, x+0.001, 1000) # sanity check
				new_obse, new_obs = obse_sampler.conditional_sample(new_obs)
				ax.plot(new_obse, new_obs, 'r.', markersize=2, alpha=1); ax.plot(np.nan, np.nan, 'r.', label='$\hat{p}(x_{ij},\sigma_{xij})$ samples (KDE)')

			### rot axis
			x = np.linspace(obse_sampler.raw_obse.min(), obse_sampler.raw_obse.max(), 100)
			ax.plot(x, x*obse_sampler.m+obse_sampler.n, 'b', alpha=0.75, label='rotation axis', lw=1)
			#ax.plot(obse_sampler.lr_x, obse_sampler.lr_y, 'b.', alpha=1, markersize=4); ax.plot(np.nan, np.nan, 'b.', label='rotation axis support samples')

		else:
			label='$p(x_{ij}'+"'"+',\sigma_{xij}'+"'"+')$'+f' {set_name} samples'
			ax.plot(obse_sampler.obse, obse_sampler.obs, 'k.', markersize=2, alpha=0.2); ax.plot(np.nan, np.nan, 'k.', label=label)
			min_obse = obse_sampler.obse.min()
			max_obse = obse_sampler.obse.max()
			pdfx = np.linspace(min_obse, max_obse, 200)
			colors = cm.viridis(np.linspace(0, 1, len(obse_sampler.distrs)))
			for p_idx in range(len(obse_sampler.distrs)):
				d = obse_sampler.distrs[p_idx]
				
				if p_idx%10==0:
					rank_ranges = obse_sampler.rank_ranges[p_idx]
					pdf_offset = rank_ranges[1] # upper of rank range
					pdfy = d['distr'].pdf(pdfx, *d['params'])
					pdfy = pdfy/pdfy.max()*pdf_scale+pdf_offset
					c = colors[p_idx]
					label = '$\hat{p}(\sigma_{xij}'+"'"+'|x_{ij}'+"'"+')$ Gaussian conditional fit'
					ax.plot(pdfx, pdfy, c=c, alpha=1, lw=1, label=label if p_idx==0 else None)
				
		if original_space:
			title = f'survey: {lcset.survey} - band: {b}'
			ax.set_xlabel('obs-error')
			ax.set_ylabel('obs' if kb==0 else None)
			ax.set_xlim([0.0, 0.05])
			ax.set_ylim([0.0, 0.3])
		else:
			title = f'survey:{lcset.survey} - band: {b}'
			ax.set_xlabel('rotated-flipped obs-error')
			ax.set_ylabel('rotated obs' if kb==0 else None)
			#ax.set_xlim([0.0, 0.02])
			#ax.set_ylim([0.0, 0.25])

		ax.set_title(title)
		ax.legend(loc='lower right')

		### multiband colors
		#ax.grid(color=C_.COLOR_DICT[b])
		[ax.spines[border].set_color(C_.COLOR_DICT[b]) for border in ['bottom', 'top', 'right', 'left']]
		[ax.spines[border].set_linewidth(2) for border in ['bottom', 'top', 'right', 'left']]

	fig.tight_layout()
	plt.show()

def plot_length_samplers(length_sampler_bdict, lcdataset, set_name:str,
	figsize:tuple=(12,5),
	):
	lcset = lcdataset[set_name]
	fig, axs = plt.subplots(1, len(lcset.band_names), figsize=figsize)
	for kb,b in enumerate(lcdataset[set_name].band_names):
		ax = axs[kb]
		length_sampler = length_sampler_bdict[b]
		lengths = length_sampler.lengths
		to_plot = {
			'original':lengths,
			'sampler':length_sampler.sample(len(lengths)),
				  }
		plot_kwargs = {
			'fig':fig,
			'ax':ax,
			'title':'$\{L_i\}_i^N$',
			'xlabel':'$L_i$ values',
			'bins':int(len(length_sampler.pdf)/2),
			'uses_density':1,
			'return_legend_patches':1,
			'label_samples':0,
			#'histtype':'stepfilled',
			'alpha':0.75,
			'xlim':(0,110),
		}
		cplots.plot_hist_bins(to_plot, **plot_kwargs)

		### multiband colors
		ax.grid(color=C_.COLOR_DICT[b])
		[ax.spines[border].set_color(C_.COLOR_DICT[b]) for border in ['bottom', 'top', 'right', 'left']]
		[ax.spines[border].set_linewidth(2) for border in ['bottom', 'top', 'right', 'left']]

	fig.tight_layout()
	plt.show()