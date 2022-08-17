.PHONY: docker
docker:
# Get the docker container from Dockerhub and run it.
	docker pull ethcomsec/rememberr-ae:latest
	docker run -it -d --name rememberr-ae-instance ethcomsec/rememberr-ae:latest
# Fetch the results from the container fs.
	mkdir -p from-docker/figures
	mkdir -p from-docker/logs
# Figures.
	docker cp rememberr-ae-instance:/rememberr/build/figures/agreementstats.png            from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/contexts.png                  from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/corrtriggers2d.png            from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/cpufix_intel_amd.png          from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/effects.png                   from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/errataperstep.png             from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/heredity_intel.png            from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/latent_errata.png             from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/msrs_intel_amd.png            from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/numtrigsrequired.png          from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/timeline.png                  from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/timeline_skylake.png          from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/triggersbetweenvendorsext.png from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/triggersbetweenvendorsfea.png from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/triggersbetweenvendors.png    from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/triggers.png                  from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/triggertimeline_relative.png  from-docker/figures
	docker cp rememberr-ae-instance:/rememberr/build/figures/workarounds_intel_amd.png     from-docker/figures
# Numbers.
	docker cp rememberr-ae-instance:/rememberr/build/logs/num_errata_intel.log from-docker/logs
	docker cp rememberr-ae-instance:/rememberr/build/logs/num_errata_amd.log from-docker/logs
	docker cp rememberr-ae-instance:/rememberr/build/logs/num_blurry_triggers.log from-docker/logs
# Stop and remove the container.
	docker kill rememberr-ae-instance
	docker rm rememberr-ae-instance
