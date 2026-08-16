import logging
import casparser
from app.adapters.casparser_adapter import CasParserAdapter

logger = logging.getLogger(__name__)

def run_pipeline(pdf_path: str, password: str, portfolio_id: str, user_id: str, filename: str):
    """
    Runs casparser and adapts the output to Supabase schemas.
    """
    logger.info("Running casparser...")
    # output="dict" or raw object. We'll use the default object format.
    cas_data = casparser.read_cas_pdf(pdf_path, password)
    
    logger.info("Adapting casparser output for Supabase...")
    adapted_data = CasParserAdapter.transform(
        cas_data=cas_data,
        portfolio_id=portfolio_id,
        user_id=user_id,
        filename=filename
    )
    
    return adapted_data
