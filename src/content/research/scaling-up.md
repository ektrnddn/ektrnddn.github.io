---
title: "Scaling up: variational autoencoders on DESI DR3"
order: 4
step: "04"
stage: "Scaling up"
scale: "Population scale, hundreds of thousands of spectra"
data: "DESI DR3 spectra"
with: "Antonella Palmese, building on Nicolaou et al. 2026"
status: "Next, after the DR1 candidate catalogue"
status_kind: planned
summary: >-
  A hand-built velocity-offset search finds only what we already know to look for. A
  variational autoencoder learns what a normal spectrum looks like and flags everything
  that is not, so binary signatures can be found at the scale of the whole survey and
  fed straight into LISA and pulsar-timing event-rate forecasts.
hook: "Let the survey tell us which spectra are strange."
key: { value: "200,000+", label: "spectra a VAE can screen for anomalies" }
sep: 0.04
sep_label: "every DESI spectrum, scored for how unusual it is"
publications: []
---
