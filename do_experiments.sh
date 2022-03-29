export ERRATA_BUILDDIR=../build
export ERRATA_ROOTDIR=..

# 1. Count the number of errata and unique errata for Intel and AMD.
cd luigicode && python3 do_counterrata.py | grep 'Number of' && cd ..

# 2. Count the number of errata with explicitly blurry triggers such as 'under complex microarchitectural conditions'.
cd luigicode && python3 do_estimblurtrg.py | grep 'Blurry triggers' && cd ..

# 3. Plot the global timeline of Intel and AMD errata (Figure 2).
cd luigicode && python3 plot_timeline.py && cd ..

# 4. Plot the errata heredity between Intel Core generations (Figure 3).
cd luigicode && python3 plot_heredityintel.py && cd ..

# 5. Plot the timeline of disclosure dates of common errata between Intel Core generations 6 ot 10 (Figure 4).
cd luigicode && python3 plot_commonskylake.py && cd ..

# 6. Plot the statistics on workarounds for Intel and AMD designs (Figure 5).
cd luigicode && python3 plot_workaroundsintelamd.py && cd ..

# 7. Plot the proportion of fixed vs. non-fixed bugs (Figure 6).
cd luigicode && python3 plot_fixednessintelamd.py && cd ..

# 8. Plot the most frequent triggers, contexts and effects (Figures 7, 11 and 12).
cd luigicode && python3 plot_trigctxeff.py && cd ..

# 9. Plot the number of required triggers (Figure 8).
cd luigicode && python3 plot_numtrigsrequired.py && cd ..

# 10. Plot the trigger cross-correlation (Figure 9).
cd luigicode && python3 plot_corrtrigctxteff.py && cd ..

# 11. Plot the trigger class timeline (Figure 10).
cd luigicode && python3 plot_triggertimeline.py && cd ..

# 12. Plot the most frequent MSRs (Figure 13).
cd luigicode && python3 plot_msrs.py && cd ..
