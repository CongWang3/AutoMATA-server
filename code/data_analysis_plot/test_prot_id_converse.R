library(clusterProfiler)
library(org.Hs.eg.db)
ls("package:org.Hs.eg.db") 
#  [1] "org.Hs.eg"                "org.Hs.eg.db"             "org.Hs.eg_dbconn"         "org.Hs.eg_dbfile"         "org.Hs.eg_dbInfo"         "org.Hs.eg_dbschema"
#  [7] "org.Hs.egACCNUM"          "org.Hs.egACCNUM2EG"       "org.Hs.egALIAS2EG"        "org.Hs.egCHR"             "org.Hs.egCHRLENGTHS"      "org.Hs.egCHRLOC"
# [13] "org.Hs.egCHRLOCEND"       "org.Hs.egENSEMBL"         "org.Hs.egENSEMBL2EG"      "org.Hs.egENSEMBLPROT"     "org.Hs.egENSEMBLPROT2EG"  "org.Hs.egENSEMBLTRANS"
# [19] "org.Hs.egENSEMBLTRANS2EG" "org.Hs.egENZYME"          "org.Hs.egENZYME2EG"       "org.Hs.egGENENAME"        "org.Hs.egGENETYPE"        "org.Hs.egGO"
# [25] "org.Hs.egGO2ALLEGS"       "org.Hs.egGO2EG"           "org.Hs.egMAP"             "org.Hs.egMAP2EG"          "org.Hs.egMAPCOUNTS"       "org.Hs.egOMIM"
# [31] "org.Hs.egOMIM2EG"         "org.Hs.egORGANISM"        "org.Hs.egPATH"            "org.Hs.egPATH2EG"         "org.Hs.egPFAM"            "org.Hs.egPMID"
# [37] "org.Hs.egPMID2EG"         "org.Hs.egPROSITE"         "org.Hs.egREFSEQ"          "org.Hs.egREFSEQ2EG"       "org.Hs.egSYMBOL"          "org.Hs.egSYMBOL2EG"
# [43] "org.Hs.egUCSCKG"          "org.Hs.egUNIPROT"

test <- toTable(org.Hs.egENSEMBL)
head(test)
#   gene_id      ensembl_id
# 1       1 ENSG00000121410
# 2       2 ENSG00000175899
# 3       3 ENSG00000291190
# 4       9 ENSG00000171428
# 5      10 ENSG00000156006
# 6      12 ENSG00000196136

ENSEMBL2EG <- toTable(org.Hs.egENSEMBL2EG)


ENSEMBLPROT <- toTable(org.Hs.egENSEMBLPROT)
ENSEMBLPROT2EG <- toTable(org.Hs.egENSEMBLPROT2EG)
#   gene_id         prot_id
# 1      10 ENSP00000286479
# 2      10 ENSP00000428416
# 3      31 ENSP00000483300
# 4      31 ENSP00000482269
# 5      31 ENSP00000478547
# 6      31 ENSP00000483969

ENSEMBLTRANS <- toTable(org.Hs.egENSEMBLTRANS)
ENSEMBLTRANS2EG <- toTable(org.Hs.egENSEMBLTRANS2EG)
#   gene_id        trans_id
# 1      10 ENST00000286479
# 2      10 ENST00000520116
# 3      31 ENST00000616317
# 4      31 ENST00000612895
# 5      31 ENST00000614428
# 6      31 ENST00000619546

ENZYME <- toTable(org.Hs.egENZYME)
ENZYME2EG <- toTable(org.Hs.egENZYME2EG)
#   gene_id ec_number
# 1       9   2.3.1.5
# 2      10   2.3.1.5
# 3      15  2.3.1.87
# 4      16   6.1.1.7
# 5      18  2.6.1.22
# 6      18  2.6.1.19

REFSEQ <- toTable(org.Hs.egREFSEQ)
REFSEQ2EG <- toTable(org.Hs.egREFSEQ2EG)  # 有NM/NP蛋白质的refseq
#   gene_id    accession
# 1       1    NM_130786
# 2       1    NP_570602
# 3       2    NM_000014
# 4       2 NM_001347423
# 5       2 NM_001347424
# 6       2 NM_001347425

SYMBOL <- toTable(org.Hs.egSYMBOL)  # 有没有蛋白质的symbol 是gene symbol
SYMBOL2EG <- toTable(org.Hs.egSYMBOL2EG)  # gene_id, gene_symbol
#   gene_id symbol
# 1       1   A1BG
# 2       2    A2M
# 3       3  A2MP1
# 4       9   NAT1
# 5      10   NAT2
# 6      11   NATP

UNIPROT <- toTable(org.Hs.egUNIPROT)
#   gene_id uniprot_id
# 1       1     A8K052  # 同一个蛋白质的二次登记入册Secondary accessions
# 2       1     P04217  # 同一个蛋白质的Primary accession
# 3       1     Q68CK0  # Secondary accessions
# 4       1     Q8IYJ6  # Secondary accessions
# 5       1     Q96P39  # Secondary accessions
# 6       1     V9HWD8


# 1个gene_id对应多个uniprot_id，说明该gene_id对应多个蛋白质，需要进一步处理
# 但是 1个gene_id又可能只对应1个refseq accession，那么refseq accession和uniprot_id的对应关系怎么办呢？

