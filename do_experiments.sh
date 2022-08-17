export ERRATA_BUILDDIR=../build
export ERRATA_ROOTDIR=..

# - Count the number of errata and unique errata for Intel and AMD.
cd luigicode && python3 do_counterrata.py | grep 'Number of' && cd ..

# - Count the number of errata with explicitly blurry triggers such as 'under complex microarchitectural conditions'.
cd luigicode && python3 do_estimblurtrg.py | grep 'Blurry triggers' && cd ..

# - Plot the global timeline of Intel and AMD errata.
cd luigicode && python3 plot_timeline.py && cd ..

# - Plot the errata heredity between Intel Core generations.
cd luigicode && python3 plot_heredityintel.py && cd ..

# - Plot the timeline of disclosure dates of common errata between Intel Core generations 6 ot 10.
cd luigicode && python3 plot_commonskylake.py && cd ..

# - Plot the forward and backward latent bugs for Intel designs.
cd luigicode && python3 plot_latentintel.py && cd ..

# - Plot the timelines of agreements between the two human classifiers.
cd luigicode && python3 plot_agreement_history.py && cd ..

# - Plot the statistics on workarounds for Intel and AMD designs.
cd luigicode && python3 plot_workaroundsintelamd.py && cd ..

# - Plot the proportion of fixed vs. non-fixed bugs.
cd luigicode && python3 plot_fixednessintelamd.py && cd ..

# - Plot the most frequent triggers, contexts and effects.
cd luigicode && python3 plot_trigctxeff.py && cd ..

# - Plot the number of required triggers.
cd luigicode && python3 plot_numtrigsrequired.py && cd ..

# - Plot the trigger cross-correlation.
cd luigicode && python3 plot_corrtrigctxteff.py && cd ..

# - Plot the trigger class comparisons between the two vendors.
cd luigicode && python3 plot_triggersbetweenvendors.py && cd ..

# - Plot the external stimuli-abstract trigger comparisons between the two vendors.
cd luigicode && python3 plot_triggersbetweenvendorsext.py && cd ..

# - Plot the specific feature-abstract trigger comparisons between the two vendors.
cd luigicode && python3 plot_triggersbetweenvendorsfea.py && cd ..

# - Plot the trigger class timeline.
cd luigicode && python3 plot_triggertimeline.py && cd ..

# - Plot the most frequent MSRs.
cd luigicode && python3 plot_msrs.py && cd ..
