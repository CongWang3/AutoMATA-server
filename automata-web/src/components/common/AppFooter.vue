<template>
  <footer id="footer" class="bg-light">
    <div class="container padding-medium">
      <div class="row">
        <div class="col-md-4 my-3">
          <h5 class="text-uppercase fw-bold mb-4">Contact us</h5>
          <p>
            <iconify-icon 
              class="social-icon text-primary fs-5 me-2" 
              icon="mdi:location"
              style="vertical-align: text-bottom"
            />
            <span class="fw-bold">Address: </span> Northwest A&amp;F University
          </p>
          <p>
            <iconify-icon 
              class="social-icon text-primary fs-5 me-2" 
              icon="ic:baseline-email"
              style="vertical-align: text-bottom"
            />
            <span class="fw-bold">Email: </span>
            wangc@nwsuaf.edu.cn <br/>
            &emsp;&emsp;&emsp;&emsp;&emsp;&nbsp;fuyi.li@nwafu.edu.cn
          </p>
        </div>
        
        <div class="col-md-2 my-3">
          <div class="footer-menu">
            <h5 class="text-uppercase fw-bold mb-4">Links</h5>
            <ul class="menu-list list-unstyled">
              <li class="menu-item mb-2">
                <router-link to="/" class="footer-link">Home</router-link>
              </li>
              <li class="menu-item mb-2">
                <router-link to="/data-process/genome" class="footer-link">Data Process</router-link>
              </li>
              <li class="menu-item mb-2">
                <router-link to="/model/train/supervised" class="footer-link">Model</router-link>
              </li>
              <li class="menu-item mb-2">
                <router-link to="/data-analysis" class="footer-link">Data Analysis</router-link>
              </li>
              <li class="menu-item mb-2">
                <router-link to="/help" class="footer-link">Help</router-link>
              </li>
            </ul>
          </div>
        </div>
        
        <div class="col-md-2 my-3">
          <div class="footer-menu">
            <h5 class="text-uppercase fw-bold mb-4">Article</h5>
            <ul class="menu-list list-unstyled">
              <li class="menu-item mb-2">
                <a 
                  href="https://github.com/ABILiLab/AutoMATA" 
                  target="_blank" 
                  class="footer-link"
                >
                  AutoMATA
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        <div class="col-md-3 my-3">
          <div class="footer-menu">
            <h5 class="text-uppercase fw-bold mb-4">Follow us</h5>
            <div class="social-links mt-4">
              <ul class="menu-list list-unstyled">
                <li class="menu-item mb-2">
                  <a 
                    href="https://www.researchgate.net/profile/Fuyi-Li" 
                    target="_blank" 
                    class="footer-link"
                  >
                    Research Gate
                  </a>
                </li>
                <li class="menu-item mb-2">
                  <a 
                    href="https://scholar.google.com/citations?user=vrADwVUAAAAJ&hl=en" 
                    target="_blank" 
                    class="footer-link"
                  >
                    Google Scholar
                  </a>
                </li>
              </ul>
              
            </div>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
// 无状态组件，不需要额外逻辑
</script>

<style scoped>
#footer {
  margin-top: auto;
  border-top: 1px solid #dee2e6;
}

.footer-link {
  color: #6c757d;
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: #0d6efd;
  text-decoration: underline;
}

.social-icon {
  transition: color 0.2s ease;
}

.social a:hover .social-icon {
  color: #0d6efd;
}

.padding-medium {
  padding: 3rem 0;
}



/* 响应式调整 */
@media (max-width: 767.98px) {
  .padding-medium {
    padding: 2rem 0;
  }
  
  .col-md-4, .col-md-2, .col-md-3 {
    text-align: center;
  }
}
</style>