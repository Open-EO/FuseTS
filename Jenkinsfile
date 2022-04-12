#!/usr/bin/env groovy

// This Jenkinsfile is used to provide snapshot builds using the VITO CI system.

@Library('lib')_

pythonPipeline {
  package_name = 'fusets'
  wipeout_workspace = true
  python_version = ["3.8"]
  extras_require = 'dev'
  upload_dev_wheels = true
  wheel_repo = 'python-openeo'
  wheel_repo_dev = 'python-openeo'
  pep440 = true
}
