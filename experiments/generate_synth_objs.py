#!/usr/bin/env python3
# -*- coding: utf-8 -*
import sys
sys.path.append('../') # or just install the module
sys.path.append('../../flaming-choripan') # or just install the module
sys.path.append('../../astro-lightcurves-handler') # or just install the module

if __name__== '__main__':
	### parser arguments
	import argparse
	from flamingchoripan.prints import print_big_bar

	parser = argparse.ArgumentParser('usage description')
	parser.add_argument('-method',  type=str, default='.', help='method')
	parser.add_argument('-kf',  type=str, default='.', help='kf')
	parser.add_argument('-setn',  type=str, default='train', help='kf')
	main_args = parser.parse_args()
	print_big_bar()

	###################################################################################################################################################
	from flamingchoripan.files import search_for_filedirs
	from synthsne import C_

	root_folder = '../../surveys-save'
	filedirs = search_for_filedirs(root_folder, fext=C_.EXT_SPLIT_LIGHTCURVE)

	###################################################################################################################################################
	import numpy as np
	from flamingchoripan.files import load_pickle, save_pickle, get_dict_from_filedir

	filedir = f'../../surveys-save/alerceZTFv7.1/survey=alerceZTFv7.1°bands=gr°mode=onlySNe.splcds'
	filedict = get_dict_from_filedir(filedir)
	root_folder = filedict['__rootdir']
	cfilename = filedict['__cfilename']
	survey = filedict['survey']
	lcdataset = load_pickle(filedir)
	print(lcdataset)

	###################################################################################################################################################
	from synthsne.generators.synthetic_datasets import generate_synthetic_dataset
	import pandas as pd
	import numpy as np
	from synthsne import C_
	import flamingchoripan.files as ff
	from flamingchoripan.progress_bars import ProgressBar
	from flamingchoripan.files import load_pickle, save_pickle
	from synthsne.distr_fittings import ObsErrorConditionalSampler
	from synthsne.plots.samplers import plot_obse_samplers
	from synthsne.plots.mcmc import plot_mcmc_prior
	from flamingchoripan.dicts import along_dict_obj_method
	from nested_dict import nested_dict
	import synthsne.generators.mcmc_priors as mp
	from synthsne import synth_method_statistics as sms
	import warnings
	warnings.filterwarnings('ignore')

	kfs = [str(kf) for kf in range(0,3)] if main_args.kf=='.' else main_args.kf
	kfs = [kfs] if isinstance(kfs, str) else kfs
	methods = ['linear-fstw', 'bspline-fstw', 'spm-mle-fstw', 'spm-mle-estw', 'spm-mcmc-fstw', 'spm-mcmc-estw'] if main_args.method=='.' else main_args.method
	methods = [methods] if isinstance(methods, str) else methods
	setns = [str(setn) for setn in ['train', 'val']] if main_args.setn=='.' else main_args.setn
	setns = [setns] if isinstance(setns, str) else setns

	for setn in setns:
		for kf in kfs:
			for method in methods:
				lcset_name = f'{kf}@{setn}'
				lcset = lcdataset[lcset_name]
				save_rootdir = f'../save/{survey}/{cfilename}/{lcset_name}'
				lcset_info = lcset.get_info()
				band_names = lcset_info['band_names']
				class_names = lcset_info['class_names']

				### export generators
				obse_sampler_bdict_full = {b:ObsErrorConditionalSampler(lcset, b) for b in band_names}
				plot_obse_samplers(lcset_name, lcset_info, obse_sampler_bdict_full, original_space=1, add_samples=0, save_filedir=f'{save_rootdir}/__obse-sampler/10.png')
				plot_obse_samplers(lcset_name, lcset_info, obse_sampler_bdict_full, original_space=0, add_samples=0, save_filedir=f'{save_rootdir}/__obse-sampler/00.png')
				plot_obse_samplers(lcset_name, lcset_info, obse_sampler_bdict_full, original_space=1, add_samples=1, save_filedir=f'{save_rootdir}/__obse-sampler/11.png')

				save_pickle(f'{save_rootdir}/obse_sampler_bdict_full.d', obse_sampler_bdict_full)
				obse_sampler_bdict = along_dict_obj_method(obse_sampler_bdict_full, 'clean')
				save_pickle(f'{save_rootdir}/obse_sampler_bdict.d', obse_sampler_bdict)

				### generate synth curves
				sd_kwargs = {
					'synthetic_samples_per_curve':C_.SYNTH_SAMPLES_PER_CURVE,
					'method':method,
					'sne_specials_df':pd.read_csv(f'../data/{survey}/sne_specials.csv'),
					'mcmc_priors':load_pickle(f'{save_rootdir}/mcmc_priors.d', return_none_if_missing=True),
				}
				uses_estw = method.split('-')[-1]=='estw'
				generate_synthetic_dataset(lcset_name, lcset, obse_sampler_bdict, uses_estw, save_rootdir, **sd_kwargs)

				### generate mcmc priors
				if method in ['spm-mle-fstw']:
					spm_classes = {
						'A':'GammaP',
						't0':'NormalP',
						'gamma':'GammaP',
						'f':'UniformP',
						'trise':'GammaP',
						'tfall':'GammaP',
					}
					mcmc_priors_full = nested_dict()
					for c in class_names:
						for b in band_names:
							for spm_p in spm_classes.keys():
								spm_p_samples = sms.get_spm_args(save_rootdir, method, spm_p, b, c)
								#print(spm_p_samples)
								mp_kwargs = {}
								if spm_p=='A':
									mp_kwargs = {'floc':0}
								mcmc_prior = getattr(mp, spm_classes[spm_p])(spm_p_samples, **mp_kwargs)
								mcmc_priors_full[b][c][spm_p] = mcmc_prior
								plot_mcmc_prior(mcmc_prior, spm_p, b, c, save_filedir=f'{save_rootdir}/__mcmc-priors/{c}_{b}_{spm_p}.png')
					
					mcmc_priors_full = mcmc_priors_full.to_dict()

					save_pickle(f'{save_rootdir}/mcmc_priors_full.d', mcmc_priors_full)
					mcmc_priors = along_dict_obj_method(mcmc_priors_full, 'clean')
					save_pickle(f'{save_rootdir}/mcmc_priors.d', mcmc_priors)