import re
from dataclasses import dataclass
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

@dataclass
class FolioSection:
    raw_lines: List[Tuple[str, int]]  # Tuple of (line_text, page_number)
    start_page: int
    end_page: int

class SectionDetector:
    def __init__(self):
        # Matches lines ending in "Mutual Fund" or "MUTUAL FUND"
        self.amc_pattern = re.compile(r"^[A-Za-z\s]+Mutual\s+Fund$", re.IGNORECASE)
        # Matches "Folio No: 123456"
        self.folio_pattern = re.compile(r"^Folio\s+No\s*:")

    def extract_sections(self, pages) -> List[FolioSection]:
        sections: List[FolioSection] = []
        current_section_lines = []
        current_start_page = 0
        
        all_lines = []
        for page in pages:
            for line in page.raw_lines:
                all_lines.append((line, page.page_number))

        i = 0
        last_amc_name = ""
        last_split_was_amc = False
        
        while i < len(all_lines):
            line, page_num = all_lines[i]
            
            is_new_section = False
            
            # Check for AMC name
            if self.amc_pattern.match(line.strip()):
                # Look ahead to see if the next non-empty line starts with "Folio No:"
                j = i + 1
                is_folio_start = False
                while j < len(all_lines) and j <= i + 15:
                    next_line, _ = all_lines[j]
                    if next_line.strip():
                        if self.folio_pattern.match(next_line.strip()):
                            is_folio_start = True
                        break
                    j += 1
                
                if is_folio_start:
                    is_new_section = True
                    last_amc_name = line.strip()
                    last_split_was_amc = True
                    
            # Check for Folio No: without AMC name (KFintech groups them)
            elif self.folio_pattern.match(line.strip()):
                if last_split_was_amc:
                    # We just split at the AMC name for this very folio, so don't split again.
                    last_split_was_amc = False
                else:
                    # This is a new grouped folio
                    is_new_section = True
                    last_split_was_amc = False
                
            if is_new_section:
                if current_section_lines and current_start_page > 0:
                    sections.append(FolioSection(
                        raw_lines=current_section_lines,
                        start_page=current_start_page,
                        end_page=page_num
                    ))
                
                current_section_lines = []
                # If this was triggered by just Folio No, inject the AMC name first
                if not self.amc_pattern.match(line.strip()) and last_amc_name:
                    current_section_lines.append((last_amc_name, page_num))
                    
                current_section_lines.append((line, page_num))
                current_start_page = page_num
                i += 1
                continue
            
            if current_section_lines:
                current_section_lines.append((line, page_num))
            
            i += 1
            
        if current_section_lines and current_start_page > 0:
            last_page = current_section_lines[-1][1]
            sections.append(FolioSection(
                raw_lines=current_section_lines,
                start_page=current_start_page,
                end_page=last_page
            ))
            
        logger.info(f"Detected {len(sections)} folio sections.")
        return sections
