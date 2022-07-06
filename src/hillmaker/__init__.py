from hillmaker.hills import make_hills

# Create root logger
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


#Create the Handler for logging data to console.
logger_handler = logging.StreamHandler()
logger_handler.setLevel(logging.INFO)

# Create a Formatter for formatting the log messages
logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the Formatter to the Handler
logger_handler.setFormatter(logger_formatter)

# Add the Handler to the Logger
logger.addHandler(logger_handler)
