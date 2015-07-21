import logging

def main():
	import argparse
	parser = argparse.ArgumentParser(description='ATACseq pipeline')
	
log = logging.getLogger('log')

def run_ATACseq_pipeline():
    log.info('Running ATACseq pipeline')
    # TODO Check to make sure we're in the correct directory
    log.info('ATACseq pipeline ran successfully')
