import os
import joblib
import pandas as pd
import requests
from flask import Flask, request, render_template_string, jsonify, redirect, url_for
from flask_cors import CORS

# -----------------
# HTML Templates
# -----------------
home_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shanvya - Gentle Maternal Wellness & Care</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --primary: hsl(355, 65%, 65%); /* Cozy Warm Rose/Terracotta */
      --primary-light: hsl(355, 85%, 95%);
      --secondary: hsl(152, 28%, 46%); /* Soothing Healing Sage */
      --secondary-light: hsl(152, 45%, 94%);
      --background: hsl(32, 45%, 98%); /* Creamy Ivory */
      --card-bg: #FFFFFF;
      --text: hsl(30, 20%, 25%); /* Cozy Charcoal */
      --text-muted: hsl(30, 12%, 48%);
      --accent: hsl(42, 65%, 63%); /* Cozy Soft Gold */
      --border: rgba(226, 135, 130, 0.15);
      --gradient-mother: linear-gradient(135deg, #FFF0F0 0%, #FFFBF5 50%, #F0F9F5 100%);
      --shadow: 0 15px 35px rgba(226, 135, 130, 0.08);
      --transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      background-color: var(--background);
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      line-height: 1.8;
      overflow-x: hidden;
    }
    
    h1, h2, h3, .brand-font {
      font-family: 'Playfair Display', serif;
      font-weight: 600;
    }
    
    /* Sticky Cozy Nav Bar */
    nav {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      z-index: 1000;
      background: rgba(250, 246, 242, 0.8);
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      border-bottom: 1px solid var(--border);
      padding: 12px 6%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: var(--transition);
      box-shadow: 0 2px 20px rgba(44, 38, 33, 0.02);
    }
    
    .nav-brand {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: var(--primary);
      transition: var(--transition);
    }
    
    .nav-brand:hover {
      transform: scale(1.02);
      opacity: 0.95;
    }
    
    .nav-logo {
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -0.5px;
    }
    
    /* Modern Floating Glassmorphic Center Links */
    .nav-links-wrapper {
      background: rgba(255, 255, 255, 0.45);
      border: 1px solid rgba(226, 135, 130, 0.18);
      border-radius: 50px;
      padding: 5px;
      box-shadow: 0 10px 30px rgba(226, 135, 130, 0.04);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }
    
    .nav-links {
      display: flex;
      gap: 5px;
      list-style: none;
      align-items: center;
    }
    
    .nav-links a {
      text-decoration: none;
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.95rem;
      padding: 10px 22px;
      border-radius: 50px;
      transition: var(--transition);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .nav-links a i {
      font-size: 1.05rem;
      color: var(--text-muted);
      opacity: 0.7;
      transition: var(--transition);
    }
    
    .nav-links a:hover {
      color: var(--primary);
      background: rgba(226, 135, 130, 0.08);
    }
    
    .nav-links a:hover i {
      color: var(--primary);
      opacity: 1;
    }
    
    /* Elegant Glowing CTA button */
    .nav-btn {
      background: linear-gradient(135deg, var(--primary), hsl(355, 65%, 58%));
      color: white;
      padding: 12px 26px;
      border-radius: 50px;
      text-decoration: none;
      font-weight: 600;
      font-size: 0.95rem;
      box-shadow: 0 6px 20px rgba(226, 135, 130, 0.22);
      transition: var(--transition);
      display: flex;
      align-items: center;
      gap: 8px;
      border: 1px solid transparent;
    }
    
    .nav-btn:hover {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 8px 25px rgba(226, 135, 130, 0.35);
    }
    
    .nav-btn i {
      transition: var(--transition);
    }
    
    .nav-btn:hover i {
      transform: rotate(15deg) scale(1.1);
    }
    
    /* Cozy Hero Section with Organic Blobs */
    .hero {
      position: relative;
      height: 100vh;
      min-height: 750px;
      display: flex;
      align-items: center;
      background: radial-gradient(circle at 80% 20%, hsla(355, 75%, 92%, 0.8), transparent 50%),
                  radial-gradient(circle at 10% 80%, hsla(152, 45%, 92%, 0.8), transparent 50%),
                  var(--background);
      padding: 0 8%;
      margin-top: 60px;
      overflow: hidden;
    }
    
    .hero-container {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 50px;
      align-items: center;
      width: 100%;
    }
    
    .hero-content {
      max-width: 650px;
      position: relative;
      z-index: 2;
    }
    
    .hero-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--primary-light);
      color: var(--primary);
      padding: 8px 18px;
      border-radius: 50px;
      font-size: 0.9rem;
      font-weight: 600;
      margin-bottom: 24px;
      border: 1px solid rgba(226, 135, 130, 0.25);
    }
    
    .hero h1 {
      font-size: 4.2rem;
      line-height: 1.15;
      color: var(--text);
      margin-bottom: 24px;
    }
    
    .hero h1 span {
      color: var(--primary);
      font-style: italic;
      font-weight: 400;
    }
    
    .hero p {
      font-size: 1.25rem;
      color: var(--text-muted);
      margin-bottom: 40px;
      font-weight: 400;
    }
    
    .hero-image-wrapper {
      position: relative;
      width: 100%;
      height: 480px;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    
    .hero-img-blob {
      position: absolute;
      width: 90%;
      height: 90%;
      background: url('/static/images/shanvya_hero.png') no-repeat center center/cover;
      border-radius: 40% 60% 60% 40% / 50% 40% 60% 50%;
      box-shadow: 0 20px 45px rgba(226, 135, 130, 0.15);
      border: 6px solid #FFF;
      animation: blobAnimate 12s ease-in-out infinite alternate;
    }
    
    @keyframes blobAnimate {
      0% { border-radius: 40% 60% 60% 40% / 50% 40% 60% 50%; }
      50% { border-radius: 60% 40% 50% 50% / 40% 60% 50% 60%; }
      100% { border-radius: 50% 50% 60% 40% / 60% 40% 60% 40%; }
    }
    
    .scroll-indicator {
      position: absolute;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      color: var(--text-muted);
      font-size: 0.9rem;
      cursor: pointer;
    }
    
    .scroll-indicator i {
      animation: bounce 2s infinite;
      color: var(--primary);
    }
    
    @keyframes bounce {
      0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(8px); }
      60% { transform: translateY(4px); }
    }
    
    /* Interactive Educational Section (Tabs Interface) */
    .tabs-section {
      padding: 120px 8%;
      background: #FFF;
      position: relative;
      z-index: 2;
    }
    
    .section-header {
      text-align: center;
      max-width: 700px;
      margin: 0 auto 60px;
    }
    
    .section-header h2 {
      font-size: 2.8rem;
      color: var(--text);
      margin-bottom: 18px;
    }
    
    .section-header p {
      font-size: 1.15rem;
      color: var(--text-muted);
    }
    
    .tabs-nav {
      display: flex;
      justify-content: center;
      gap: 15px;
      margin-bottom: 50px;
      background: var(--background);
      padding: 8px;
      border-radius: 50px;
      width: fit-content;
      margin-left: auto;
      margin-right: auto;
      border: 1px solid var(--border);
    }
    
    .tab-trigger {
      background: transparent;
      border: none;
      font-family: inherit;
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      padding: 10px 24px;
      border-radius: 30px;
      transition: var(--transition);
    }
    
    .tab-trigger.active {
      color: var(--primary);
      background: #FFF;
      box-shadow: 0 6px 15px rgba(226, 135, 130, 0.08);
    }
    
    .tab-content {
      display: none;
      animation: tabFadeIn 0.5s ease-out forwards;
    }
    
    .tab-content.active {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 50px;
      align-items: center;
    }
    
    @keyframes tabFadeIn {
      from { opacity: 0; transform: translateY(15px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .tab-text h3 {
      font-size: 2.4rem;
      line-height: 1.25;
      margin-bottom: 20px;
      color: var(--text);
    }
    
    .tab-text p {
      font-size: 1.15rem;
      color: var(--text-muted);
      margin-bottom: 25px;
    }
    
    .tab-visual-card {
      background: var(--primary-light);
      border-radius: 28px;
      padding: 40px;
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }
    
    .tab-visual-card::after {
      content: '';
      position: absolute;
      top: -50px; right: -50px;
      width: 150px; height: 150px;
      border-radius: 50%;
      background: rgba(226, 135, 130, 0.15);
    }
    
    /* Stats & Global Dashboard Section */
    .dashboard-section {
      padding: 120px 8%;
      background: var(--gradient-mother);
      position: relative;
      z-index: 2;
    }
    
    .stats-layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 60px;
      align-items: center;
    }
    
    .stats-graphic-container {
      position: relative;
      height: 480px;
      border-radius: 36px;
      overflow: hidden;
      box-shadow: 0 20px 45px rgba(226, 135, 130, 0.15);
      border: 6px solid #FFF;
      background: url('/static/images/shanvya_support.png') no-repeat center center/cover;
    }
    
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 25px;
    }
    
    .dashboard-card {
      background: #FFF;
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 30px;
      box-shadow: var(--shadow);
      transition: var(--transition);
    }
    
    .dashboard-card:hover {
      transform: translateY(-5px);
      border-color: var(--primary);
    }
    
    .db-value {
      font-family: 'Playfair Display', serif;
      font-size: 3.2rem;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 8px;
    }
    
    .db-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 5px;
    }
    
    .db-desc {
      font-size: 0.95rem;
      color: var(--text-muted);
    }
    
    /* Clinical Methodology Section */
    .clinical-section {
      padding: 120px 8%;
      background: #FFF;
      z-index: 2;
      position: relative;
    }
    
    .clinical-card {
      background: linear-gradient(135deg, #FFFBF9 0%, #FFF0EE 100%);
      border: 1px solid var(--border);
      border-radius: 36px;
      padding: 60px;
      box-shadow: var(--shadow);
    }
    
    .clinical-layout {
      display: grid;
      grid-template-columns: 0.8fr 1.2fr;
      gap: 50px;
      align-items: center;
    }
    
    .clinical-visual {
      background: var(--primary);
      color: #FFF;
      padding: 45px;
      border-radius: 28px;
      text-align: center;
      box-shadow: 0 15px 35px rgba(226, 135, 130, 0.2);
    }
    
    .clinical-visual i {
      font-size: 4rem;
      color: #FFF;
      margin-bottom: 20px;
    }
    
    .clinical-visual h3 {
      font-size: 1.8rem;
      margin-bottom: 10px;
    }
    
    .clinical-visual p {
      font-size: 0.95rem;
      opacity: 0.85;
    }
    
    .clinical-info h2 {
      font-size: 2.8rem;
      line-height: 1.2;
      margin-bottom: 20px;
    }
    
    .clinical-info p {
      font-size: 1.15rem;
      color: var(--text-muted);
      margin-bottom: 30px;
    }
    
    .clinical-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    
    .clinical-item {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 500;
      font-size: 1.05rem;
    }
    
    .clinical-item i {
      color: var(--secondary);
      font-size: 1.3rem;
    }
    
    /* Immersive Maternal CTA Section */
    .cta-pathway {
      padding: 130px 8%;
      background: radial-gradient(circle at center, hsla(355, 75%, 93%, 0.5) 0%, transparent 70%), var(--background);
      text-align: center;
      position: relative;
      z-index: 2;
    }
    
    .pathway-card {
      max-width: 850px;
      margin: 0 auto;
      background: #FFF;
      border: 1px solid var(--border);
      border-radius: 36px;
      padding: 70px 40px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }
    
    .pathway-card::before {
      content: '';
      position: absolute;
      bottom: -100px; right: -100px;
      width: 250px; height: 250px;
      border-radius: 50%;
      background: var(--primary-light);
      opacity: 0.6;
    }
    
    .pathway-card::after {
      content: '';
      position: absolute;
      top: -100px; left: -100px;
      width: 250px; height: 250px;
      border-radius: 50%;
      background: var(--secondary-light);
      opacity: 0.6;
    }
    
    .pathway-icon {
      width: 70px;
      height: 70px;
      border-radius: 50%;
      background: var(--primary-light);
      color: var(--primary);
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 2rem;
      margin: 0 auto 24px;
    }
    
    .pathway-card h2 {
      font-size: 3rem;
      line-height: 1.25;
      margin-bottom: 20px;
      position: relative;
      z-index: 2;
    }
    
    .pathway-card p {
      font-size: 1.2rem;
      color: var(--text-muted);
      max-width: 650px;
      margin: 0 auto 40px;
      position: relative;
      z-index: 2;
    }
    
    /* Glowing Cozy Button */
    .gentle-btn {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      background: linear-gradient(135deg, var(--primary), hsl(355, 65%, 58%));
      color: white;
      padding: 18px 45px;
      border-radius: 50px;
      text-decoration: none;
      font-size: 1.25rem;
      font-weight: 600;
      box-shadow: 0 10px 25px rgba(226, 135, 130, 0.4);
      transition: var(--transition);
      border: none;
      cursor: pointer;
      position: relative;
      z-index: 2;
    }
    
    .gentle-btn:hover {
      transform: translateY(-3px) scale(1.03);
      box-shadow: 0 15px 30px rgba(226, 135, 130, 0.5);
    }
    
    .gentle-btn i {
      transition: var(--transition);
    }
    
    .gentle-btn:hover i {
      transform: translateX(6px);
    }
    
    /* Footer */
    footer {
      border-top: 1px solid var(--border);
      padding: 50px 8%;
      text-align: center;
      background: #FFF;
      color: var(--text-muted);
      z-index: 2;
      position: relative;
    }
    
    footer .logo {
      color: var(--primary);
      font-weight: 700;
      font-size: 1.7rem;
      margin-bottom: 12px;
      letter-spacing: -0.5px;
    }
    
    /* Responsive styling */
    @media (max-width: 992px) {
      .hero-container {
        grid-template-columns: 1fr;
        text-align: center;
      }
      .hero-content {
        max-width: 100%;
      }
      .hero h1 {
        font-size: 3rem;
      }
      .hero-image-wrapper {
        height: 380px;
      }
      .tab-content.active {
        grid-template-columns: 1fr;
      }
      .stats-layout {
        grid-template-columns: 1fr;
      }
      .clinical-layout {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>

  <!-- Sticky Cozy Navbar -->
  <nav>
    <a href="#" class="nav-brand">
      <i class="fa-solid fa-spa" style="margin-right: 10px; font-size: 1.8rem; color: var(--primary);"></i>
      <span class="nav-logo brand-font">Shanvya</span>
    </a>
    <div class="nav-links-wrapper">
      <ul class="nav-links">
        <li><a href="#explore"><i class="fa-solid fa-leaf"></i> Explore</a></li>
        <li><a href="#impact"><i class="fa-solid fa-globe"></i> Global Insights</a></li>
        <li><a href="#clinical"><i class="fa-solid fa-stethoscope"></i> Clinical Standard</a></li>
      </ul>
    </div>
    <a href="/test" class="nav-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> Gentle Check-in</a>
  </nav>

  <!-- Hero Section -->
  <section class="hero">
    <div class="hero-container">
      <div class="hero-content" data-aos="fade-right" data-aos-duration="1200">
        <div class="hero-badge">
          <i class="fa-solid fa-heart"></i> Cozy Safe Haven for New Mothers
        </div>
        <h1>Caring for the One Who <span>Cares.</span></h1>
        <p>A gentle, private, and clinically validated digital platform built to screen for postpartum distress and guide you lovingly toward healing.</p>
        <div class="hero-ctas">
          <a href="#pathway" class="gentle-btn">
            Begin Quiet Assessment <i class="fa-solid fa-arrow-right"></i>
          </a>
        </div>
      </div>
      <div class="hero-image-wrapper" data-aos="zoom-in" data-aos-duration="1500">
        <div class="hero-img-blob"></div>
      </div>
    </div>
  </section>

  <!-- Interactive Educational Tabs (Developer Detail) -->
  <section class="tabs-section" id="explore">
    <div class="section-header" data-aos="fade-up" data-aos-duration="1000">
      <h2>Understanding Postpartum Depression</h2>
      <p>PPD is a treatable clinical condition, not a personal flaw. Explore critical educational insights below.</p>
    </div>
    
    <div class="tabs-nav" data-aos="fade-up" data-aos-duration="1000">
      <button class="tab-trigger active" onclick="switchTab(event, 'ppd-tab')">What is PPD?</button>
      <button class="tab-trigger" onclick="switchTab(event, 'effects-tab')">The Hidden Symptoms</button>
      <button class="tab-trigger" onclick="switchTab(event, 'importance-tab')">Why Care Matters</button>
    </div>
    
    <!-- Tab 1 -->
    <div class="tab-content active" id="ppd-tab">
      <div class="tab-text">
        <h3>A complex medical transition, not a personal weakness.</h3>
        <p>Postpartum depression (PPD) is a serious, highly complex mental health condition that arises following childbirth. It is triggered by rapid, severe drops in estrogen and progesterone, coupled with extreme sleep deprivation and environmental adjustments.</p>
      </div>
      <div class="tab-visual-card">
        <h3 class="brand-font" style="font-size: 1.7rem; margin-bottom: 12px; color: var(--primary)">Key Indicator</h3>
        <p>Unlike the temporary "baby blues" which fade in two weeks, PPD is persistent, deeply affecting daily operations, physical energy, and maternal safety.</p>
      </div>
    </div>
    
    <!-- Tab 2 -->
    <div class="tab-content" id="effects-tab">
      <div class="tab-text">
        <h3>Understanding how PPD manifests.</h3>
        <p>Symptoms are often masked by the fatigue of new parenthood. They include a profound sense of emptiness, persistent crying, severe anxiety, and extreme feelings of guilt or inadequacy that inhibit connecting with the baby.</p>
      </div>
      <div class="tab-visual-card">
        <h3 class="brand-font" style="font-size: 1.7rem; margin-bottom: 12px; color: var(--primary)">Clinical Scope</h3>
        <p>PPD symptoms can start within the first few weeks after birth or build up gradually, sometimes appearing up to a year later.</p>
      </div>
    </div>
    
    <!-- Tab 3 -->
    <div class="tab-content" id="importance-tab">
      <div class="tab-text">
        <h3>Why screening and timely care save lives.</h3>
        <p>If left untreated, postpartum depression can lead to severe emotional distress for the mother, impact marital bonding, and hinder the newborn's early cognitive and emotional development.</p>
      </div>
      <div class="tab-visual-card">
        <h3 class="brand-font" style="font-size: 1.7rem; margin-bottom: 12px; color: var(--primary)">Recovery Path</h3>
        <p>Early identification through diagnostic questionnaires leads directly to support plans, therapy, and medical support—ensuring a 100% path back to wellness.</p>
      </div>
    </div>
  </section>

  <!-- Cozy Dashboard Section -->
  <section class="dashboard-section" id="impact">
    <div class="stats-layout">
      <div class="stats-graphic-container" data-aos="fade-right" data-aos-duration="1200"></div>
      <div class="stats-content" data-aos="fade-left" data-aos-duration="1200">
        <div class="section-header" style="text-align: left; margin-bottom: 30px; max-width: 100%">
          <h2>Maternal Mental Health Insights</h2>
          <p>Postpartum depression represents a global crisis. These statistics emphasize why highly accessible, digital screening standardizations are so crucial.</p>
        </div>
        
        <div class="dashboard-grid">
          <div class="dashboard-card">
            <div class="db-value">1 in 7</div>
            <div class="db-title">New Mothers</div>
            <div class="db-desc">Suffer clinically from postpartum depression worldwide.</div>
          </div>
          
          <div class="dashboard-card">
            <div class="db-value">15%</div>
            <div class="db-title">Global Rate</div>
            <div class="db-desc">Prevalence index across both high and low-income countries.</div>
          </div>
          
          <div class="dashboard-card">
            <div class="db-value">80%</div>
            <div class="db-title">Undetected</div>
            <div class="db-desc">Cases fail to be screened or treated due to social stigma.</div>
          </div>
          
          <div class="dashboard-card">
            <div class="db-value">100%</div>
            <div class="db-title">Recoverable</div>
            <div class="db-desc">PPD is fully manageable through early detection and care.</div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Clinical Methodology -->
  <section class="clinical-section" id="clinical">
    <div class="clinical-card" data-aos="fade-up" data-aos-duration="1200">
      <div class="clinical-layout">
        <div class="clinical-visual">
          <i class="fa-solid fa-stethoscope"></i>
          <h3>Clinically Backed</h3>
          <p>Edinburgh Postnatal Depression Scale</p>
        </div>
        <div class="clinical-info">
          <h2>Grounded in World-Class Clinical Science</h2>
          <p>Our assessment suite is fully based on the <strong>Edinburgh Postnatal Depression Scale (EPDS)</strong>, developed in 1987. It represents the medical gold-standard utilized by health systems, obstetricians, and pediatricians globally to identify clinical risk factors securely and sensitively.</p>
          <div class="clinical-grid">
            <div class="clinical-item"><i class="fa-solid fa-circle-check"></i> Sensitive & Private</div>
            <div class="clinical-item"><i class="fa-solid fa-circle-check"></i> Medically Proven</div>
            <div class="clinical-item"><i class="fa-solid fa-circle-check"></i> Emotionally Centered</div>
            <div class="clinical-item"><i class="fa-solid fa-circle-check"></i> Standardized scoring</div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Cozy Pathway CTA -->
  <section class="cta-pathway" id="pathway">
    <div class="pathway-card" data-aos="zoom-in" data-aos-duration="1200">
      <div class="pathway-icon">
        <i class="fa-solid fa-spa"></i>
      </div>
      <h2>Self-Care Reflection Space</h2>
      <p>Step away from the demands of the day for a brief 3-minute check-in. It is entirely anonymous, private, and powered by an advanced predictive model. A compassionate, warm AI counselor will be available instantly upon completion if you need immediate comfort.</p>
      <a href="/test" class="gentle-btn">
        Step into Your Healing Space <i class="fa-solid fa-wand-magic-sparkles"></i>
      </a>
    </div>
  </section>

  <!-- Footer -->
  <footer>
    <div class="logo brand-font">Shanvya</div>
    <p>&copy; 2026 Shanvya Maternal Wellness Systems. Cozy care for mothers.</p>
  </footer>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>
  <script>
    AOS.init({ once: true });
    
    function switchTab(evt, tabId) {
      const contents = document.querySelectorAll('.tab-content');
      contents.forEach(content => content.classList.remove('active'));
      
      const triggers = document.querySelectorAll('.tab-trigger');
      triggers.forEach(trigger => trigger.classList.remove('active'));
      
      document.getElementById(tabId).classList.add('active');
      evt.currentTarget.classList.add('active');
    }
  </script>
</body>
</html>
"""

test_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shanvya - Gentle Wellness Check-in</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --primary: hsl(355, 65%, 65%);
      --primary-light: hsl(355, 85%, 95%);
      --background: hsl(32, 45%, 98%);
      --text: hsl(30, 20%, 25%);
      --text-muted: hsl(30, 12%, 48%);
      --border: rgba(226, 135, 130, 0.22);
      --shadow: 0 20px 50px rgba(226, 135, 130, 0.08);
      --transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      background: linear-gradient(-45deg, #FFC6C2, #FFE4D3, #CBEFE2, #E8F5D5);
      background-size: 400% 400%;
      animation: gradientBG 15s ease infinite;
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px 20px;
      position: relative;
      overflow: hidden;
    }
    
    @keyframes gradientBG {
      0% {background-position: 0% 50%;}
      50% {background-position: 100% 50%;}
      100% {background-position: 0% 50%;}
    }
    
    /* Dreamy Decorative Ambient Orbs */
    .orb-1 {
      position: absolute;
      top: -10%; left: -10%;
      width: 400px; height: 400px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.4);
      filter: blur(50px);
      z-index: 0;
      pointer-events: none;
      animation: drift 20s infinite alternate;
    }
    
    .orb-2 {
      position: absolute;
      bottom: -10%; right: -10%;
      width: 400px; height: 400px;
      border-radius: 50%;
      background: rgba(226, 135, 130, 0.2);
      filter: blur(50px);
      z-index: 0;
      pointer-events: none;
      animation: drift 25s infinite alternate-reverse;
    }
    
    @keyframes drift {
      from { transform: translate(0, 0) scale(1); }
      to { transform: translate(40px, 40px) scale(1.1); }
    }
    
    .nav-header {
      margin-bottom: 25px;
      text-align: center;
      position: relative;
      z-index: 2;
    }
    
    .brand-logo {
      font-family: 'Playfair Display', serif;
      font-size: 2.6rem;
      font-weight: 700;
      color: var(--text);
      text-decoration: none;
      text-shadow: 0 2px 8px rgba(255, 255, 255, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }
    
    .wizard-card {
      background: radial-gradient(circle at top left, #FFFBF9, #FFFFFF 70%);
      border: 2px solid var(--border);
      border-radius: 36px;
      width: 100%;
      max-width: 650px;
      padding: 50px;
      box-shadow: 0 25px 60px rgba(226, 135, 130, 0.12);
      position: relative;
      z-index: 2;
    }
    
    .progress-bar-container {
      width: 100%;
      height: 8px;
      background: rgba(226, 135, 130, 0.12);
      border-radius: 10px;
      margin-bottom: 45px;
      overflow: hidden;
    }
    
    .progress-bar {
      height: 100%;
      background: linear-gradient(90deg, var(--primary), #FFB7B2);
      width: 0%;
      transition: var(--transition);
      box-shadow: 0 2px 10px rgba(226, 135, 130, 0.2);
    }
    
    .question-card {
      display: none;
    }
    
    .question-card.active {
      display: block;
      animation: fadeIn 0.5s ease-out;
    }
    
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(15px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .maternal-accent {
      display: flex;
      justify-content: center;
      color: var(--primary);
      font-size: 1.6rem;
      margin-bottom: 12px;
      animation: gentlePulse 2s infinite alternate;
    }
    
    @keyframes gentlePulse {
      from { transform: scale(1); opacity: 0.8; }
      to { transform: scale(1.1); opacity: 1; }
    }
    
    .q-number {
      font-size: 0.9rem;
      color: var(--primary);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      text-align: center;
      margin-bottom: 15px;
    }
    
    .q-text {
      font-family: 'Playfair Display', serif;
      font-size: 1.9rem;
      line-height: 1.35;
      color: var(--text);
      text-align: center;
      margin-bottom: 35px;
      font-style: italic;
    }
    
    /* Cozy custom pillowy tactile options */
    .options-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 40px;
    }
    
    .option-label {
      display: flex;
      align-items: center;
      border: 1.5px solid var(--border);
      border-radius: 20px;
      padding: 20px 26px;
      cursor: pointer;
      transition: var(--transition);
      font-size: 1.1rem;
      font-weight: 600;
      position: relative;
      background: #FFF;
      box-shadow: 0 4px 10px rgba(226, 135, 130, 0.02);
    }
    
    .option-label:hover {
      background: var(--primary-light);
      border-color: var(--primary);
      transform: translateY(-2px);
      box-shadow: 0 6px 15px rgba(226, 135, 130, 0.08);
    }
    
    .option-label input[type="radio"] {
      position: absolute;
      opacity: 0;
    }
    
    .custom-radio {
      width: 22px;
      height: 22px;
      border: 2px solid var(--border);
      border-radius: 50%;
      margin-right: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: var(--transition);
      background: #FFF;
    }
    
    .option-label input[type="radio"]:checked + .custom-radio {
      border-color: var(--primary);
      background: var(--primary);
    }
    
    .option-label input[type="radio"]:checked + .custom-radio::after {
      content: '';
      width: 8px;
      height: 8px;
      background: #FFF;
      border-radius: 50%;
    }
    
    .option-label input[type="radio"]:checked ~ span {
      color: var(--primary);
    }
    
    .option-label.selected {
      background: var(--primary-light);
      border-color: var(--primary);
      box-shadow: 0 8px 25px rgba(226, 135, 130, 0.1);
    }
    
    /* Cozy dynamic subtitles at bottom of wizard */
    .wiz-subtitle {
      text-align: center;
      font-size: 0.95rem;
      color: var(--text-muted);
      margin-bottom: 35px;
      font-style: italic;
      font-weight: 500;
      min-height: 25px;
      transition: var(--transition);
    }
    
    /* Navigation buttons */
    .wizard-buttons {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      border-top: 1px solid var(--border);
      padding-top: 35px;
    }
    
    .wiz-btn {
      padding: 15px 34px;
      border-radius: 50px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: var(--transition);
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    
    .wiz-btn-prev {
      background: #FFF;
      color: var(--text-muted);
      border: 1.5px solid var(--border);
    }
    
    .wiz-btn-prev:hover {
      background: var(--primary-light);
      color: var(--primary);
    }
    
    .wiz-btn-next {
      background: var(--text);
      color: white;
      box-shadow: 0 4px 15px rgba(44, 38, 33, 0.15);
    }
    
    .wiz-btn-next:hover {
      background: var(--primary);
      box-shadow: 0 8px 25px rgba(226, 135, 130, 0.35);
      transform: translateY(-2px);
    }
    
    .wiz-btn-submit {
      background: var(--primary);
      color: white;
      box-shadow: 0 8px 25px rgba(226, 135, 130, 0.3);
      display: none;
    }
    
    .wiz-btn-submit:hover {
      background: hsl(355, 65%, 58%);
      transform: translateY(-2px);
    }
    
    /* Result styling */
    .result-container {
      text-align: center;
      padding: 20px 0;
    }
    
    .result-icon {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      background: var(--primary-light);
      color: var(--primary);
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 2.5rem;
      margin: 0 auto 24px;
      box-shadow: 0 4px 15px rgba(226, 135, 130, 0.15);
    }
    
    .result-heading {
      font-family: 'Playfair Display', serif;
      font-size: 2.2rem;
      margin-bottom: 20px;
      color: var(--text);
    }
    
    .result-text {
      color: var(--text-muted);
      font-size: 1.15rem;
      margin-bottom: 35px;
      line-height: 1.8;
      max-width: 500px;
      margin-left: auto;
      margin-right: auto;
    }
    
    .result-action {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      background: var(--primary);
      color: white;
      padding: 18px 40px;
      border-radius: 50px;
      text-decoration: none;
      font-weight: 600;
      box-shadow: 0 10px 25px rgba(226, 135, 130, 0.35);
      transition: var(--transition);
    }
    
    .result-action:hover {
      background: hsl(355, 65%, 58%);
      transform: translateY(-2px);
    }
  </style>
</head>
<body>

  <div class="orb-1"></div>
  <div class="orb-2"></div>

  <div class="nav-header">
    <a href="/" class="brand-logo"><i class="fa-solid fa-spa" style="color: var(--primary);"></i> Shanvya</a>
  </div>

  <div class="wizard-card">
    {% if prediction %}
    <!-- Prediction Screen -->
    <div class="result-container">
      <div class="result-icon">
        <i class="fa-solid fa-heart"></i>
      </div>
      <h2 class="result-heading">Assessment Completed</h2>
      
      {% if 'Positive' in prediction %}
      <p class="result-text">Our prediction model suggests a high chance that you are experiencing postpartum distress. This is completely normal and treatable. We have arranged a private counseling space for you right now.</p>
      <a href="/chat" class="result-action">Speak with our Counselor <i class="fa-solid fa-comments"></i></a>
      {% else %}
      <p class="result-text">Your responses indicate a lower likelihood of clinical postpartum depression at this time. However, remember to always prioritize self-care and reach out if you feel overwhelmed.</p>
      <a href="/" class="result-action">Back to Home <i class="fa-solid fa-home"></i></a>
      {% endif %}
    </div>
    {% else %}
    <!-- Wizard Form -->
    <div class="progress-bar-container">
      <div class="progress-bar" id="progressBar"></div>
    </div>
    
    <form id="wizardForm" action="/test" method="post">
      {% for q in questions %}
      <div class="question-card" id="qCard-{{ loop.index0 }}">
        <div class="maternal-accent"><i class="fa-solid fa-seedling"></i></div>
        <div class="q-number">Step {{ loop.index }} of 9</div>
        <div class="q-text">{{ q }}</div>
        
        <div class="options-container">
          <label class="option-label" onclick="selectOption(this)">
            <input type="radio" name="q-{{ loop.index0 }}" value="Yes" required>
            <span class="custom-radio"></span>
            <span>Yes, most of the time</span>
          </label>
          
          <label class="option-label" onclick="selectOption(this)">
            <input type="radio" name="q-{{ loop.index0 }}" value="No">
            <span class="custom-radio"></span>
            <span>No, not at all</span>
          </label>
          
          {% if 'Maybe' in q or 'Sometimes' in q %}
          <label class="option-label" onclick="selectOption(this)">
            <input type="radio" name="q-{{ loop.index0 }}" value="Maybe">
            <span class="custom-radio"></span>
            <span>Sometimes / Maybe</span>
          </label>
          {% endif %}
        </div>
      </div>
      {% endfor %}
      
      <div class="wiz-subtitle" id="wizSubtitle"></div>
      
      <div class="wizard-buttons">
        <button type="button" class="wiz-btn wiz-btn-prev" id="prevBtn" onclick="navigateStep(-1)" disabled><i class="fa-solid fa-chevron-left"></i> Back</button>
        <button type="button" class="wiz-btn wiz-btn-next" id="nextBtn" onclick="navigateStep(1)">Next <i class="fa-solid fa-chevron-right"></i></button>
        <button type="submit" class="wiz-btn wiz-btn-submit" id="submitBtn">Submit Assessment <i class="fa-solid fa-circle-check"></i></button>
      </div>
    </form>
    {% endif %}
  </div>

  <script>
    let currentStep = 0;
    const totalSteps = 9;
    
    const subtitles = [
      "Take a soft, quiet breath. You are doing wonderfully, dear.",
      "We are here with you. Every single feeling you have is fully valid.",
      "Be gentle with your heart. Your honesty is the first step to healing.",
      "You are never alone in this space. We are listening with deep care.",
      "Maternal wellness is built on small, brave moments of reflection.",
      "We are moving forward together, step by gentle step.",
      "This quiet moment for yourself is a beautiful gift of love.",
      "Almost there, sweet mother. You are doing so, so well.",
      "Thank you for sharing your heart. Let us evaluate your wellness now."
    ];
    
    function showStep(stepIndex) {
      const cards = document.querySelectorAll('.question-card');
      cards.forEach((card, index) => {
        card.classList.toggle('active', index === stepIndex);
      });
      
      // Update Buttons
      document.getElementById('prevBtn').disabled = (stepIndex === 0);
      if (stepIndex === totalSteps - 1) {
        document.getElementById('nextBtn').style.display = 'none';
        document.getElementById('submitBtn').style.display = 'inline-flex';
      } else {
        document.getElementById('nextBtn').style.display = 'inline-flex';
        document.getElementById('submitBtn').style.display = 'none';
      }
      
      // Update Progress Bar
      const percentage = ((stepIndex) / (totalSteps - 1)) * 100;
      document.getElementById('progressBar').style.width = percentage + '%';
      
      // Update cozy subtitle
      document.getElementById('wizSubtitle').textContent = subtitles[stepIndex];
    }
    
    function navigateStep(direction) {
      if (direction === 1) {
        const activeCard = document.querySelector('.question-card.active');
        const checkedInput = activeCard.querySelector('input[type="radio"]:checked');
        if (!checkedInput) {
          alert("Please select an option to proceed.");
          return;
        }
      }
      
      currentStep += direction;
      showStep(currentStep);
    }
    
    function selectOption(element) {
      const options = element.parentElement.querySelectorAll('.option-label');
      options.forEach(opt => opt.classList.remove('selected'));
      
      element.classList.add('selected');
      const radio = element.querySelector('input[type="radio"]');
      radio.checked = true;
    }
    
    if (document.getElementById('qCard-0')) {
      showStep(0);
    }
  </script>
</body>
</html>
"""

chat_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shanvya - Gentle Counseling Space</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --primary: hsl(355, 65%, 65%);
      --primary-light: hsl(355, 85%, 95%);
      --secondary: hsl(152, 28%, 46%);
      --secondary-light: hsl(152, 45%, 94%);
      --background: hsl(32, 45%, 98%);
      --text: hsl(30, 20%, 25%);
      --text-muted: hsl(30, 12%, 48%);
      --border: rgba(226, 135, 130, 0.22);
      --shadow: 0 15px 35px rgba(226, 135, 130, 0.08);
      --transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      background: linear-gradient(135deg, #FFC6C2, #B8F2E6);
      font-family: 'Outfit', sans-serif;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      color: var(--text);
      padding: 20px;
      position: relative;
      overflow: hidden;
    }
    
    /* Decorative drifting clouds in background */
    .cloud-bg {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.35);
      filter: blur(40px);
      z-index: 0;
      pointer-events: none;
    }
    
    #container {
      background: rgba(255, 255, 255, 0.95);
      width: 100%;
      max-width: 600px;
      height: 90vh;
      max-height: 800px;
      border-radius: 32px;
      border: 2px solid var(--border);
      box-shadow: 0 25px 60px rgba(44, 38, 33, 0.12);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
      z-index: 2;
    }
    
    .chat-header {
      background: linear-gradient(90deg, #FFF9F8 0%, #FFEBE8 100%);
      border-bottom: 1px solid var(--border);
      padding: 22px 28px;
      display: flex;
      align-items: center;
      gap: 15px;
    }
    
    .avatar-wrapper {
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: var(--primary-light);
      display: flex;
      justify-content: center;
      align-items: center;
      color: var(--primary);
      font-size: 1.6rem;
      border: 2px solid white;
      box-shadow: 0 4px 10px rgba(226, 135, 130, 0.15);
      position: relative;
    }
    
    .avatar-wrapper::after {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      border-radius: 50%;
      border: 2px solid var(--primary);
      animation: pulseRadar 2s infinite;
    }
    
    @keyframes pulseRadar {
      0% { transform: scale(1); opacity: 1; }
      100% { transform: scale(1.3); opacity: 0; }
    }
    
    .header-info h3 {
      font-family: 'Playfair Display', serif;
      font-size: 1.4rem;
      color: var(--text);
      font-weight: 700;
    }
    
    .header-info p {
      font-size: 0.88rem;
      color: var(--secondary);
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    
    .header-info p::before {
      content: '';
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--secondary);
    }
    
    #chatbox {
      flex: 1;
      overflow-y: auto;
      padding: 25px;
      background: radial-gradient(circle at 10% 10%, hsla(355, 75%, 96%, 0.9), transparent 60%),
                  radial-gradient(circle at 90% 90%, hsla(152, 45%, 96%, 0.9), transparent 60%),
                  #FFFBF9;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .message {
      max-width: 78%;
      display: flex;
      flex-direction: column;
      animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .message.user {
      align-self: flex-end;
      align-items: flex-end;
    }
    
    .message.bot {
      align-self: flex-start;
      align-items: flex-start;
    }
    
    .bubble {
      padding: 16px 24px;
      border-radius: 24px;
      font-size: 1.05rem;
      line-height: 1.6;
    }
    
    .user .bubble {
      background: linear-gradient(135deg, var(--primary), #FFA39E);
      color: white;
      border-bottom-right-radius: 4px;
      box-shadow: 0 8px 20px rgba(226, 135, 130, 0.22);
    }
    
    .bot .bubble {
      background: #ffffff;
      color: var(--text);
      border: 1px solid var(--border);
      border-left: 4px solid var(--primary);
      border-bottom-left-radius: 4px;
      box-shadow: 0 4px 15px rgba(44, 38, 33, 0.02);
    }
    
    .msg-time {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 5px;
    }
    
    .input-area {
      background: white;
      border-top: 1px solid var(--border);
      padding: 22px;
      display: flex;
      gap: 12px;
      align-items: center;
    }
    
    .input-wrapper {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;
    }
    
    input[type="text"] {
      width: 100%;
      padding: 16px 24px;
      border-radius: 50px;
      border: 1.5px solid var(--border);
      font-size: 1.05rem;
      font-family: inherit;
      outline: none;
      transition: var(--transition);
      background: hsl(32, 20%, 98%);
    }
    
    input[type="text"]:focus {
      border-color: var(--primary);
      background: white;
      box-shadow: 0 0 0 4px var(--primary-light);
    }
    
    .send-btn {
      background: var(--primary);
      color: white;
      border: none;
      width: 52px;
      height: 52px;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 1.25rem;
      transition: var(--transition);
      box-shadow: 0 6px 15px rgba(226, 135, 130, 0.25);
    }
    
    .send-btn:hover {
      background: hsl(355, 65%, 58%);
      transform: scale(1.05);
    }
    
    .voice-btn {
      background: hsl(32, 20%, 90%);
      color: var(--text);
      border: none;
      width: 52px;
      height: 52px;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 1.25rem;
      transition: var(--transition);
    }
    
    .voice-btn:hover {
      background: hsl(32, 20%, 85%);
      color: var(--primary);
    }
    
    .crisis-card {
      background: #FFF5F5;
      border: 1px dashed rgba(226, 135, 130, 0.5);
      border-radius: 16px;
      padding: 14px 20px;
      font-size: 0.85rem;
      color: hsl(0, 75%, 35%);
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 15px 25px 0;
      box-shadow: 0 4px 10px rgba(226, 135, 130, 0.02);
    }
    
    .crisis-card a {
      color: inherit;
      font-weight: 700;
      text-decoration: underline;
    }
  </style>
</head>
<body>

  <!-- Cloud background visual orbs -->
  <div class="cloud-bg" style="width: 300px; height: 300px; top: -50px; left: -50px;"></div>
  <div class="cloud-bg" style="width: 350px; height: 350px; bottom: -80px; right: -80px;"></div>

  <div id="container">
    <div class="chat-header">
      <div class="avatar-wrapper">
        <i class="fa-solid fa-hands-holding-child"></i>
      </div>
      <div class="header-info">
        <h3 class="brand-font">Shanvya Counsel</h3>
        <p>Warm Care Companion</p>
      </div>
    </div>
    
    <div class="crisis-card">
      <i class="fa-solid fa-heart" style="color: var(--primary); font-size: 1.2rem;"></i>
      <span>Remember, dear mother, you are never alone. If you need immediate, compassionate human support, these helplines are always here: <strong>AASRA (<a href="tel:91-22-27546669">91-22-27546669</a>)</strong> or <strong>SNEHA (<a href="tel:91-44-24640050">91-44-24640050</a>)</strong></span>
    </div>
    
    <div id="chatbox">
      <!-- Welcome message -->
      <div class="message bot">
        <div class="bubble">
          Hello, dear mother. Welcome to this quiet, safe space. I am Shanvya, your gentle companion here to listen, support, and stand by you. Please feel free to share anything on your mind. How are you feeling today?
        </div>
      </div>
    </div>
    
    <div class="input-area">
      <div class="input-wrapper">
        <input type="text" id="userInput" placeholder="Share your thoughts softly here..." onkeypress="handleKeyPress(event)">
      </div>
      <button class="voice-btn" id="voiceButton" onclick="startVoiceInput()"><i class="fa-solid fa-microphone"></i></button>
      <button class="send-btn" onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i></button>
    </div>
  </div>

  <script>
    function handleKeyPress(event) {
      if (event.key === "Enter") {
        sendMessage();
      }
    }
    
    async function sendMessage() {
      const input = document.getElementById("userInput");
      const message = input.value;
      if (!message.trim()) return;

      addMessage("user", message);
      input.value = "";

      addTyping();

      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });

      const data = await res.json();
      removeTyping();
      addMessage("bot", data.response);
    }

    function addMessage(type, text) {
      const chatbox = document.getElementById("chatbox");
      const msg = document.createElement("div");
      msg.className = `message ${type}`;

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = text;
      
      const time = document.createElement("div");
      time.className = "msg-time";
      const now = new Date();
      time.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      msg.appendChild(bubble);
      msg.appendChild(time);
      chatbox.appendChild(msg);
      chatbox.scrollTop = chatbox.scrollHeight;
    }

    function addTyping() {
      const chatbox = document.getElementById("chatbox");
      const typingDiv = document.createElement("div");
      typingDiv.className = "message bot";
      typingDiv.id = "typing";

      const typingBubble = document.createElement("div");
      typingBubble.className = "bubble";
      typingBubble.innerHTML = "<i class='fa-solid fa-circle-notch fa-spin'></i> <i>Listening carefully...</i>";
      
      typingDiv.appendChild(typingBubble);
      chatbox.appendChild(typingDiv);
      chatbox.scrollTop = chatbox.scrollHeight;
    }

    function removeTyping() {
      const typing = document.getElementById("typing");
      if (typing) typing.remove();
    }

    function startVoiceInput() {
      const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
      recognition.lang = 'en-IN';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById("userInput").value = transcript;
        sendMessage();
      };

      recognition.onerror = (event) => {
        alert("Voice input error: " + event.error);
      };

      recognition.start();
    }
  </script>
</body>
</html>
"""

# -----------------
# App Initialization
# -----------------
app = Flask(__name__)
CORS(app)

# Attempt to load model
try:
    model = joblib.load("models/catboostmodel_balanced.joblib")
    print("Model loaded successfully.")
except FileNotFoundError:
    print("Model not found! Please run 'python train_model.py' first.")
    model = None

questions = [
    "Do you have problems concentrating or making decisions?",
    "Have you experienced overeating or loss of appetite?",
    "Do you often feel anxious?",
    "Do you feel a sense of guilt? (Yes/No/Maybe)",
    "Are you having problems bonding with your baby? (Yes/No/Sometimes)",
    "Have you ever attempted or thought about suicide?",
    "Do you have trouble sleeping?",
    "Do you often feel sad or hopeless? (Yes/No/Sometimes)",
    "Do you feel irritable towards your baby or partner? (Yes/No/Sometimes)"
]

def preprocess_responses(responses):
    if not model:
        raise Exception("Model is not loaded.")
        
    features = {col: 0 for col in model.feature_names_}
    
    mappings = [
        ("Problems concentrating or making decision_Yes", responses[0] if len(responses)>0 else None),
        ("Overeating or loss of appetite_Yes", responses[1] if len(responses)>1 else None),
        ("Feeling anxious_Yes", responses[2] if len(responses)>2 else None),
        ("Feeling of guilt_Yes", responses[3] if len(responses)>3 and responses[3] == "Yes" else None),
        ("Feeling of guilt_Maybe", responses[3] if len(responses)>3 and responses[3] == "Maybe" else None),
        ("Problems of bonding with baby_Yes", responses[4] if len(responses)>4 and responses[4] == "Yes" else None),
        ("Problems of bonding with baby_Sometimes", responses[4] if len(responses)>4 and (responses[4] == "Sometimes" or responses[4] == "Maybe") else None),
        ("Suicide attempt_Yes", responses[5] if len(responses)>5 else None),
        ("Trouble sleeping at night_Yes", responses[6] if len(responses)>6 else None),
        ("Feeling sad or Tearful_Yes", responses[7] if len(responses)>7 and responses[7] == "Yes" else None),
        ("Feeling sad or Tearful_Sometimes", responses[7] if len(responses)>7 and (responses[7] == "Sometimes" or responses[7] == "Maybe") else None),
        ("Irritable towards baby & partner_Yes", responses[8] if len(responses)>8 and responses[8] == "Yes" else None),
        ("Irritable towards baby & partner_Sometimes", responses[8] if len(responses)>8 and (responses[8] == "Sometimes" or responses[8] == "Maybe") else None)
    ]

    for feature_name, condition in mappings:
        if condition == "Yes" and feature_name in features:
            features[feature_name] = 1

    return pd.DataFrame([features])[model.feature_names_]


@app.route("/")
def home():
    return render_template_string(home_template)

@app.route("/test", methods=["GET", "POST"])
def test():
    if request.method == "POST":
        try:
            if not model:
                return "Error: Model not loaded. Train the model first."
                
            responses = [request.form.get(f"q-{i}") for i in range(9)]
            input_data = preprocess_responses(responses)
            prediction = model.predict(input_data)[0]
            result = "Positive for Postpartum Depression (PPD)" if prediction == 1 else "Negative for Postpartum Depression (PPD)"

            return render_template_string(test_template, questions=questions, prediction=result)
        except Exception as e:
            return f"Error processing form: {e}"
    else:
        return render_template_string(test_template, questions=questions)

@app.route("/chat", methods=["GET"])
def chat():
    return render_template_string(chat_template)

@app.route("/chat", methods=["POST"])
def chat_response():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "I'm here when you're ready to talk. 😊"})

    # Empathy-driven fallback system when network/API is offline or failing
    def get_supportive_fallback(user_msg):
        msg = user_msg.lower()
        if any(w in msg for w in ["suicide", "kill", "die", "end my life", "harm"]):
            return "Dear mother, please know that you are not alone and there is deep care available for you. Although my connection to the AI core is currently resting, please reach out immediately to AASRA (91-22-27546669) or SNEHA (91-44-24640050). They are there to listen and hold space for you. Your life is precious. ❤️"
        if any(w in msg for w in ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]):
            return "Hello there, sweet mother. I am having a tiny connection issue with my AI core, but I wanted to immediately send a warm hug your way. How are you and your little one feeling today? ❤️"
        if any(w in msg for w in ["sad", "depressed", "cry", "crying", "anxious", "scared", "fear", "hurt"]):
            return "I can feel how heavy things are for you right now, and I am sending you so much love. Although I'm experiencing a brief network hiccup, please know that your feelings are completely valid and it is okay to not be okay. Try to take slow, gentle breaths. You are doing the best you can, and that is more than enough. 🌸"
        if any(w in msg for w in ["tired", "exhausted", "sleep", "weary", "drain", "fatigue"]):
            return "Being a mother is beautiful, but it is also incredibly exhausting. Please let yourself rest without guilt. I am having a temporary connection issue, but I want you to remember that taking care of yourself is part of taking care of your baby. Sleep, rest, and be gentle with yourself. 💤"
        return "I am right here with you. I'm currently having a small connection difficulty with my server, but I want you to know you are doing an incredibly beautiful job. Take a deep, gentle breath. You are never alone, and your feelings matter. 🌸"

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        # Graceful warm fallback instead of raw configuration error
        return jsonify({"response": get_supportive_fallback(user_input)})

    prompt = f"""
You are a warm, emotionally intelligent counselor supporting users through conversation.

Your behavior depends on the user's input:
- If the message is casual (like "hi", "hello", "good morning", etc.), respond casually and supportively.
- If the user expresses emotional distress, analyze the emotional tone and reply empathetically.
- Avoid assuming sadness unless the user explicitly or clearly shows it.
- Maintain natural, conversational tone like a real human.

If the user expresses suicidal thoughts or crisis, suggest contacting Indian mental health helplines like AASRA (91-22-27546669) or SNEHA (91-44-24640050).

User: {user_input}
Counselor:"""

    headers = {
        "Authorization": f"Bearer {hf_token}"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.7,
            "top_p": 0.95,
            "repetition_penalty": 1.2
        }
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        response_json = response.json()

        if isinstance(response_json, list) and 'generated_text' in response_json[0]:
            generated_text = response_json[0]['generated_text']
            final_response = generated_text.split("Counselor:", 1)[-1].strip()
        else:
            final_response = get_supportive_fallback(user_input)

        return jsonify({"response": final_response})

    except Exception:
        # Always fall back to a warm, supportive, rule-based counselor message if network fails
        return jsonify({"response": get_supportive_fallback(user_input)})

if __name__ == "__main__":
    app.run(port=5001, debug=True)
