<template>
    <div class="index-page">
        <!-- Hero Section -->
        <section id="hero">
            <div class="container-fluid">
                <div class="row align-items-center">
                    <div class="col-lg-4 offset-lg-1 padding-large">
                        <div class="hero-content">
                            <h1 class="hero-title">
                                AutoMATA
                            </h1>
                            <h2 class="hero-subtitle">
                                a deep learning-enhanced bioinformatics platform
                            </h2>
                            <p class="hero-description">
                                for multi-omics data processing, exploration and modelling
                            </p>
                            <button type="button" class="btn btn-primary px-5 py-3 mt-4 w-220" @click="goToAnalysis">
                                GO to train and analysis
                            </button>
                        </div>
                    </div>
                    <div class="col-lg-7" style="padding: 0;">
                        <img src="/images/background.png" alt="AutoMATA Platform" class="img-fluid hero-image"
                            fetchpriority="high">
                    </div>
                </div>
            </div>
        </section>
    </div>


    <!-- Service Section -->
    <section id="service" class="padding-medium">
        <div class="container">
            <div class="text-center">
                <h2 class="display-5 fw-semibold">We provide</h2>
            </div>

            <div class="row g-md-4 mt-2">
                <div class="col-md-4 mt-4">
                    <div class="services-element p-4 rounded-3 d-flex">
                        <div>
                            <i class="service-icon fs-1">👤</i>
                        </div>
                        <div class="ps-3">
                            <h4 class="py-2 m-0">Data Process</h4>
                            <p>Data processing functions for gene, mRNA, protein expression data</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mt-4">
                    <div class="services-element p-4 rounded-3 d-flex">
                        <div>
                            <i class="service-icon fs-1">🏆</i>
                        </div>
                        <div class="ps-3">
                            <h4 class="py-2 m-0">Model</h4>
                            <p>Training and application of deep learning models</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mt-4">
                    <div class="services-element p-4 rounded-3 d-flex">
                        <div>
                            <i class="service-icon fs-1">👥</i>
                        </div>
                        <div class="ps-3">
                            <h4 class="py-2 m-0">Data Analyse</h4>
                            <p>Multiple data visualisation and analysis functions</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="text-center" style="margin-top: 50px;">
                <h2 class="display-5 fw-semibold">Visitor map</h2>
            </div>

            <div style="height: 400px; width: 100%; justify-content: center; display: flex; align-items: center;">
                <div style="text-align: center;">
                    <a href="https://mapmyvisitors.com/web/1c0h6" title="Visit tracker" target="_blank" rel="noopener">
                        <img src="https://mapmyvisitors.com/map.png?d=1TQ78vsdHNfZUbF05j2pZNDFqKuRfJibShpoQVkLxrM&cl=ffffff"
                            alt="Visitor Map" loading="lazy" width="600" height="300"
                            style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
                            @error="handleImageError">
                    </a>
                </div>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
const goToAnalysis = () => {
    // 这里可以导航到分析页面，暂时使用 window.open 模拟原来的行为
    window.open('/analysis_train.php', '_blank')
}

const handleImageError = (event: Event) => {
    const img = event.target as HTMLImageElement
    img.style.display = 'none'
}
</script>

<style scoped>
.index-page {
    width: 100%;
}

.padding-large {
    padding: 4rem 0 2rem 0;
}

.padding-medium {
    padding: 3rem 0;
}

.services-element {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.services-element:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.service-icon {
    color: #0d6efd;
}

@media (max-width: 991.98px) {
    .padding-large {
        padding: 4rem 0 2rem 0;
    }

    .padding-medium {
        padding: 2rem 0;
    }
}

.hero-content {
    text-align: left;
    margin-bottom: 2rem;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    color: #2c3e50;
    margin-bottom: 0.5rem;
    line-height: 1.1;
    letter-spacing: -0.5px;
}

.hero-subtitle {
    font-size: 1.5rem;
    font-weight: 600;
    color: #3498db;
    margin-bottom: 0.75rem;
    line-height: 1.3;
}

.hero-description {
    font-size: 1.1rem;
    color: #7f8c8d;
    line-height: 1.6;
    margin-bottom: 0;
}

@media (max-width: 991.98px) {
    .hero-title {
        font-size: 2.8rem;
    }

    .hero-subtitle {
        font-size: 1.3rem;
    }

    .hero-description {
        font-size: 1rem;
    }
}

@media (max-width: 767.98px) {
    .hero-content {
        text-align: center;
    }

    .hero-title {
        font-size: 2.2rem;
    }

    .hero-subtitle {
        font-size: 1.1rem;
    }

    .hero-description {
        font-size: 0.95rem;
    }
}

.padding-medium {
    padding: 1.5rem 0;
}

.hero-image {
    /* border-radius: 12px; */
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
    margin-top: -100px;
}

@media (max-width: 767.98px) {
    .padding-large {
        padding: 3rem 0 1.5rem 0;
    }
}
</style>