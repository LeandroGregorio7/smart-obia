# 🧠 Smart OBIA for QGIS

![QGIS Version](https://img.shields.io/badge/QGIS-3.10%2B-green?logo=qgis)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Scikit-Learn](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-orange)
![License](https://img.shields.io/badge/License-GPLv3-lightgrey)

**Smart OBIA** is an advanced Object-Based Image Analysis (OBIA) and Machine Learning classification toolkit, natively integrated into the QGIS Processing Toolbox. Unlike traditional approaches that classify individual pixels, Smart OBIA focuses on classifying **objects (polygons)**, utilizing their spectral signatures, geometry, and texture. This plugin was developed to bridge the gap between spatial vector data and high-performance machine learning, allowing you to train, classify, and statistically validate your imagery entirely within the QGIS environment.

---

## 🎯 What makes Smart OBIA different?

The QGIS ecosystem offers several classification tools. **Smart OBIA** stands out compared to traditional approaches and existing plugins, as detailed in the following table:

| Feature | Traditional (Pixel-Based) | Standard GEOBIA Plugins | Deep Learning Plugins | 🧠 Smart OBIA |
| :--- | :--- | :--- | :--- | :--- |
| **Output Quality** | Often suffers from "salt-and-pepper" noise. | Good, but usually limited to basic algorithms. | Excellent, but borders can be fuzzy without post-processing. | **Excellent.** Classifies sharp, pre-segmented polygons. |
| **Hardware Required** | Low (CPU). | Medium (CPU). | Extremely High (Requires powerful GPUs). | **Low/Medium (CPU).** Highly optimized ensemble trees. |
| **Data Requirements** | Few pixels needed. | Moderate sample polygons. | Massive training datasets (thousands of samples). | **Moderate.** Achieves high accuracy with limited training samples. |
| **Explainability** | Black-box or basic thresholding. | Black-box. | Complete Black-box. | **Transparent (SHAP).** Tells you exactly *which* band drove the decision. |
| **Validation** | Basic error matrix. | External tools required. | Built-in (often python-only metrics). | **Automated HTML Dashboards** directly inside QGIS. |

---

## ⚙️ Algorithms & Core Functions

Smart OBIA provides a robust suite of machine learning algorithms to handle various cartographic challenges. Each function is optimized to read QGIS vectors efficiently:

*   🌲 **Random Forest (RF):** The gold standard for remote sensing. Builds an ensemble of decision trees. Excellent for high-dimensional data and highly resistant to overfitting.
*   🌳 **Extra Trees (ET):** Similar to Random Forest, but introduces more randomness in the cut-off points. Often faster and performs exceptionally well on noisy datasets.
*   🚀 **CatBoost:** A high-performance gradient boosting library that handles categorical features automatically and provides state-of-the-art accuracy for complex spatial patterns.
*   📐 **Support Vector Machine (SVM):** Uses geometric hyperplanes to separate classes in 3D space. Highly effective for complex, non-linear boundaries.
*   📊 **Gaussian Mixture Models (GMM):** A probabilistic clustering model that assumes all data points are generated from a mixture of Gaussian distributions. Great for continuous spectral transitions.
*   📈 **Automated SHAP Validation:** Every classification generates an interactive HTML Validation Report featuring Overall Accuracy, F1-Scores, Spatial Confusion Matrices, and **Feature Importance (SHAP)** graphs for model interpretability [5].

---

## 🌍 Real-World Applications

Smart OBIA is highly versatile and can be applied to various remote sensing workflows:

*   **Precision Agriculture:** Crop identification, disease mapping, and yield estimation based on spectral and structural indices.
*   **Forestry & Conservation:** Detection of specific tree species (e.g., *Dipteryx alata* / Baru), deforestation tracking, and biomass estimation.
*   **Urban Planning:** Mapping impervious surfaces, roof types, and urban green spaces.
*   **Hydrology:** Mapping water bodies, wetlands, and flooded areas using radar (SAR) or optical imagery.

---

## 🎥 Video Tutorials (Step-by-Step)

Watch these quick tutorials to master the Smart OBIA workflow from start to finish:

### 1. Calculate Radiometric Index
*(Learn how to process your raw raster data to generate key spectral indices like NDVI, EVI, or NDWI to enhance feature detection.)*
<p align="left">
  <a href="https://github.com/user-attachments/assets/c5a0210d-e79b-4d90-956d-cdbe0a0f359e" target="_blank">
    <img src="https://github.com/user-attachments/assets/c5a0210d-e79b-4d90-956d-cdbe0a0f359e" alt="Watch Video 1" width="400" />
  </a>
</p>

### 2. Texture Extractor & Spectral Signature Analyst
*(How to extract advanced texture metrics and analyze the spectral signatures of your segmented objects to prepare the training dataset.)*
<p align="left">
  <a href="https://github.com/user-attachments/assets/74312f19-2393-4f95-8a4f-abf842788cb4" target="_blank">
    <img src="https://github.com/user-attachments/assets/74312f19-2393-4f95-8a4f-abf842788cb4" alt="Watch Video 2" width="400" />
  </a>
</p>

### 3. Stack Bands
*(Learn how to correctly layer and stack your spectral and texture bands to create a comprehensive multi-dimensional input for the machine learning model.)*
<p align="left">
  <a href="https://github.com/user-attachments/assets/82e3257f-ed15-42af-b22d-780c40d39736" target="_blank">
    <img src="https://github.com/user-attachments/assets/82e3257f-ed15-42af-b22d-780c40d39736" alt="Watch Video 3" width="400" />
  </a>
</p>

### 4. Classification
*(Run the final classification by choosing from a powerful set of Machine Learning algorithms, including **Random Forest, Extra Trees, CatBoost, SVM, and GMM**. This step also generates automated validation dashboards and SHAP importance reports to ensure model transparency.)*
<p align="left">
  <a href="https://github.com/user-attachments/assets/e0ed97b4-fc58-48a5-9556-12dd2c735e84" target="_blank">
    <img src="https://github.com/user-attachments/assets/e0ed97b4-fc58-48a5-9556-12dd2c735e84" alt="Watch Video 4" width="400" />
  </a>
</p>

---

## 🛠️ Requirements & Installation

### ⚠️ Prerequisite: Scikit-Learn & CatBoost
Smart OBIA relies on the **Scikit-Learn** and **CatBoost** libraries. You must install them in your QGIS Python environment before activating the plugin.

**Windows Installation:**
1.  Close QGIS.
2.  Open the Windows Start Menu, search for **OSGeo4W Shell**, right-click it, and select **Run as Administrator**.
3.  Run the following command exactly as written:
    ```cmd
    python -m pip install scikit-learn catboost
    ```

**Linux/macOS Installation:**
1.  Open a terminal and run:
    ```bash
    python3 -m pip install scikit-learn catboost
    ```

### Smart OBIA Plugin Installation
1.  In QGIS, go to `Plugins > Manage and Install Plugins...`.
2.  In the `All` tab, search for "Smart OBIA".
3.  Select the plugin and click `Install Plugin`.
4.  After installation, Smart OBIA will be available in the QGIS Processing Toolbox.

---

## 📚 References

[1] GEOBIA. (n.d.). *GEOBIA vs Pixel-Based Classification | Object vs Pixel Analysis*. Available at: [https://geobia.com/geobia-vs-pixel-based](https://geobia.com/geobia-vs-pixel-based)
[2] Taylor & Francis. (n.d.). *a case study in a citrus orchard and an onion crop*. Available at: [https://www.tandfonline.com/doi/full/10.1080/22797254.2021.1951623](https://www.tandfonline.com/doi/full/10.1080/22797254.2021.1951623)
[3] QGIS: Deepness. (n.d.). *Home — QGIS: Deepness: Deep Neural Remote Sensing 0.7 ...*. Available at: [https://qgis-plugin-deepness.readthedocs.io/](https://qgis-plugin-deepness.readthedocs.io/)
[4] QGIS: Deepness. (n.d.). *Home — QGIS: Deepness: Deep Neural Remote Sensing 0.7 ...*. Available at: [https://qgis-plugin-deepness.readthedocs.io/](https://qgis-plugin-deepness.readthedocs.io/)
[5] SHAP. (n.d.). *An introduction to explainable AI with Shapley values — SHAP latest ...*. Available at: [https://shap.readthedocs.io/en/latest/example_notebooks/overviews/An%20introduction%20to%20explainable%20AI%20with%20Shapley%20values.html](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/An%20introduction%20to%20explainable%20AI%20with%20Shapley%20values.html)
