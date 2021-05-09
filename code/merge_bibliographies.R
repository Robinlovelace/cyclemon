# Aim: check for duplicate .bib entries and merge bibliographies
bib1 = as.data.frame(RefManageR::ReadBib("paper/cyclemon.bib"))
bib2 = as.data.frame(RefManageR::ReadBib("paper/cyclemon2.bib"))
summary(bib2$title %in% bib1$title)

# Solution: Zotero import -> remove duplicates
