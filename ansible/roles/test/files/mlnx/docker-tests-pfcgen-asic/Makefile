all: save

build: Dockerfile
        docker build -t pfc_storm .

save: build
        docker save pfc_storm:latest | gzip >pfc_storm.tgz
