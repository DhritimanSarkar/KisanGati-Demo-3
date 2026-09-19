from flask import Flask, render_template_string, request, redirect, url_for, jsonify, flash, session
import sqlite3
from datetime import datetime
import json
import re
import os
from functools import wraps
import hmac

app = Flask(__name__)
app.secret_key = "sih26032-demo-secret"
DB = "procurement.db"

TRANSLATIONS = {'en': {'name': 'English', 'home': 'Home', 'register_nav': 'Register', 'queue_nav': 'Live Queue', 'status_nav': 'Status', 'hero_title': 'Smart Procurement,<br>Where Innovation Takes Root', 'hero_desc': 'Register your crop, book a time slot, receive a digital token and track procurement and payment — all from one place.', 'book': 'Book Your Slot →', 'centre': '📍 Procurement Centre — Today', 'current_token': 'Current token being served', 'waiting': 'Estimated waiting farmers: 6', 'centre_status': 'Centre status:', 'open': '● Open', 'how_title': 'How KisanGati Works', 'how_desc': 'A digital workflow for transparent agricultural procurement.', 'reg': '1. Farmer Registration', 'reg_desc': 'Register your farmer details, crop and expected quantity online.', 'slot': '2. Slot Booking', 'slot_desc': 'Choose an available procurement slot instead of waiting in a large crowd.', 'token': '3. Digital Token', 'token_desc': 'Get a token and see your live position in the queue.', 'notify': '4. Smart Notifications', 'notify_desc': 'Receive alerts when your turn is approaching.', 'proc': '5. Procurement Tracking', 'proc_desc': 'Track quality check, weighing and procurement progress.', 'pay': '6. Payment Tracking', 'pay_desc': 'View expected amount and whether payment is processing or credited.', 'reg_title': 'Farmer Registration & Slot Booking', 'reg_sub': 'Enter your details to receive a digital token.', 'farmer_name': 'Farmer Name', 'mobile': 'Mobile Number', 'farmer_id': 'Farmer ID', 'crop': 'Crop', 'quantity': 'Quantity (quintals)', 'available_slot': 'Available Slot', 'submit': 'Register & Get Token', 'today_slots': "Today's Slots", 'slots_help': 'Slots help distribute farmer arrivals and reduce congestion.', 'live': '🔴 Live Queue Management', 'live_sub': 'Farmers can check their position instead of waiting blindly.', 'serving': 'Now serving', 'next': 'Next:', 'sample': 'Your sample token', 'away': '6 positions away', 'simulate': 'Simulate Next Farmer', 'status_title': '📦 Procurement & Payment Status', 'status_sub': 'Complete transparency from booking to payment.', 'booking': 'Booking', 'arrived': 'Arrived', 'queue': 'Queue', 'quality': 'Quality Check', 'weighing': 'Weighing', 'procurement': 'Procurement', 'payment_processing': 'Payment Processing', 'payment_received': 'Payment Received', 'completed': 'Completed ✓', 'processing': 'Processing', 'recent': 'Recent Registrations', 'recent_sub': 'Demo data stored in SQLite.', 'status': 'Status', 'no_reg': 'No registrations yet.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 Demo | Smart Automation for Agricultural Procurement', 'success': 'Registration successful! Your digital token is {token}. You will receive an alert when your turn approaches.', 'queue_alert': 'Queue updated! Now serving: {current}\\nYour token P104 is approximately {ahead} positions away.', 'slots_left': '{n} slots left', 'full': 'Full'}, 'hi': {'name': 'हिन्दी', 'home': 'होम', 'register_nav': 'पंजीकरण', 'queue_nav': 'लाइव कतार', 'status_nav': 'स्थिति', 'hero_title': 'स्मार्ट खरीद,<br>जहाँ नवाचार जड़ें जमाता है', 'hero_desc': 'अपनी फसल पंजीकृत करें, समय स्लॉट बुक करें, डिजिटल टोकन पाएं और खरीद व भुगतान की स्थिति एक ही जगह देखें।', 'book': 'स्लॉट बुक करें →', 'centre': '📍 खरीद केंद्र — आज', 'current_token': 'वर्तमान टोकन', 'waiting': 'अनुमानित प्रतीक्षारत किसान: 6', 'centre_status': 'केंद्र की स्थिति:', 'open': '● खुला', 'how_title': 'KisanGati कैसे काम करता है', 'how_desc': 'पारदर्शी कृषि खरीद के लिए डिजिटल प्रक्रिया।', 'reg': '1. किसान पंजीकरण', 'reg_desc': 'अपनी किसान जानकारी, फसल और अनुमानित मात्रा ऑनलाइन दर्ज करें।', 'slot': '2. स्लॉट बुकिंग', 'slot_desc': 'भीड़ में इंतज़ार करने के बजाय उपलब्ध खरीद स्लॉट चुनें।', 'token': '3. डिजिटल टोकन', 'token_desc': 'टोकन पाएं और कतार में अपनी लाइव स्थिति देखें।', 'notify': '4. स्मार्ट सूचनाएं', 'notify_desc': 'आपकी बारी आने पर सूचना प्राप्त करें।', 'proc': '5. खरीद की निगरानी', 'proc_desc': 'गुणवत्ता जांच, वजन और खरीद की प्रगति देखें।', 'pay': '6. भुगतान की निगरानी', 'pay_desc': 'अपेक्षित राशि और भुगतान की स्थिति देखें।', 'reg_title': 'किसान पंजीकरण और स्लॉट बुकिंग', 'reg_sub': 'डिजिटल टोकन पाने के लिए अपनी जानकारी भरें।', 'farmer_name': 'किसान का नाम', 'mobile': 'मोबाइल नंबर', 'farmer_id': 'किसान आईडी', 'crop': 'फसल', 'quantity': 'मात्रा (क्विंटल)', 'available_slot': 'उपलब्ध स्लॉट', 'submit': 'पंजीकरण करें और टोकन पाएं', 'today_slots': 'आज के स्लॉट', 'slots_help': 'स्लॉट किसानों के आगमन को व्यवस्थित करते हैं और भीड़ कम करते हैं।', 'live': '🔴 लाइव कतार प्रबंधन', 'live_sub': 'बिना बेवजह इंतज़ार किए अपनी कतार की स्थिति देखें।', 'serving': 'अभी चल रहा है', 'next': 'अगला:', 'sample': 'आपका नमूना टोकन', 'away': '6 स्थान दूर', 'simulate': 'अगले किसान का सिमुलेशन', 'status_title': '📦 खरीद और भुगतान की स्थिति', 'status_sub': 'बुकिंग से भुगतान तक पूरी पारदर्शिता।', 'booking': 'बुकिंग', 'arrived': 'पहुंचे', 'queue': 'कतार', 'quality': 'गुणवत्ता जांच', 'weighing': 'वजन', 'procurement': 'खरीद', 'payment_processing': 'भुगतान प्रक्रिया', 'payment_received': 'भुगतान प्राप्त', 'completed': 'पूरा हुआ ✓', 'processing': 'प्रक्रिया में', 'recent': 'हाल के पंजीकरण', 'recent_sub': 'डेमो डेटा SQLite में संग्रहीत है।', 'status': 'स्थिति', 'no_reg': 'अभी कोई पंजीकरण नहीं।', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 डेमो | कृषि खरीद स्वचालन', 'success': 'पंजीकरण सफल! आपका डिजिटल टोकन {token} है। आपकी बारी आने पर आपको सूचना मिलेगी।', 'queue_alert': 'कतार अपडेट हुई! अभी चल रहा है: {current}\\nआपका टोकन P104 लगभग {ahead} स्थान दूर है।', 'slots_left': '{n} स्लॉट बाकी', 'full': 'भरा हुआ'}, 'bn': {'name': 'বাংলা', 'home': 'হোম', 'register_nav': 'নিবন্ধন', 'queue_nav': 'লাইভ সারি', 'status_nav': 'স্থিতি', 'hero_title': 'স্মার্ট ক্রয়,<br>যেখানে উদ্ভাবন শিকড় গাড়ে', 'hero_desc': 'ফসল নিবন্ধন করুন, সময়ের স্লট বুক করুন, ডিজিটাল টোকেন নিন এবং ক্রয় ও পেমেন্টের অবস্থা এক জায়গায় দেখুন।', 'book': 'স্লট বুক করুন →', 'centre': '📍 ক্রয় কেন্দ্র — আজ', 'current_token': 'বর্তমান টোকেন', 'waiting': 'আনুমানিক অপেক্ষারত কৃষক: 6', 'centre_status': 'কেন্দ্রের অবস্থা:', 'open': '● খোলা', 'how_title': 'KisanGati কীভাবে কাজ করে', 'how_desc': 'স্বচ্ছ কৃষি ক্রয়ের জন্য ডিজিটাল ব্যবস্থা।', 'reg': '1. কৃষক নিবন্ধন', 'reg_desc': 'কৃষকের তথ্য, ফসল ও আনুমানিক পরিমাণ অনলাইনে নিবন্ধন করুন।', 'slot': '2. স্লট বুকিং', 'slot_desc': 'ভিড়ে অপেক্ষা না করে উপলব্ধ ক্রয় স্লট বেছে নিন।', 'token': '3. ডিজিটাল টোকেন', 'token_desc': 'টোকেন নিন এবং সারিতে আপনার অবস্থান দেখুন।', 'notify': '4. স্মার্ট নোটিফিকেশন', 'notify_desc': 'আপনার পালা কাছে এলে বিজ্ঞপ্তি পান।', 'proc': '5. ক্রয় ট্র্যাকিং', 'proc_desc': 'মান পরীক্ষা, ওজন ও ক্রয়ের অগ্রগতি দেখুন।', 'pay': '6. পেমেন্ট ট্র্যাকিং', 'pay_desc': 'প্রত্যাশিত অর্থ ও পেমেন্টের অবস্থা দেখুন।', 'reg_title': 'কৃষক নিবন্ধন ও স্লট বুকিং', 'reg_sub': 'ডিজিটাল টোকেন পেতে আপনার তথ্য দিন।', 'farmer_name': 'কৃষকের নাম', 'mobile': 'মোবাইল নম্বর', 'farmer_id': 'কৃষক আইডি', 'crop': 'ফসল', 'quantity': 'পরিমাণ (কুইন্টাল)', 'available_slot': 'উপলব্ধ স্লট', 'submit': 'নিবন্ধন করুন ও টোকেন নিন', 'today_slots': 'আজকের স্লট', 'slots_help': 'স্লট কৃষকদের আগমন ভাগ করে দেয় এবং ভিড় কমায়।', 'live': '🔴 লাইভ সারি ব্যবস্থাপনা', 'live_sub': 'অপেক্ষা না করে আপনার সারির অবস্থান দেখুন।', 'serving': 'এখন চলছে', 'next': 'পরবর্তী:', 'sample': 'আপনার নমুনা টোকেন', 'away': '6 অবস্থান দূরে', 'simulate': 'পরবর্তী কৃষক সিমুলেট করুন', 'status_title': '📦 ক্রয় ও পেমেন্টের অবস্থা', 'status_sub': 'বুকিং থেকে পেমেন্ট পর্যন্ত সম্পূর্ণ স্বচ্ছতা।', 'booking': 'বুকিং', 'arrived': 'পৌঁছেছেন', 'queue': 'সারি', 'quality': 'মান পরীক্ষা', 'weighing': 'ওজন', 'procurement': 'ক্রয়', 'payment_processing': 'পেমেন্ট প্রক্রিয়াধীন', 'payment_received': 'পেমেন্ট প্রাপ্ত', 'completed': 'সম্পন্ন ✓', 'processing': 'প্রক্রিয়াধীন', 'recent': 'সাম্প্রতিক নিবন্ধন', 'recent_sub': 'ডেমো ডেটা SQLite-তে সংরক্ষিত।', 'status': 'অবস্থা', 'no_reg': 'এখনও কোনো নিবন্ধন নেই।', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 ডেমো | কৃষি ক্রয় স্বয়ংক্রিয়করণ', 'success': 'নিবন্ধন সফল! আপনার ডিজিটাল টোকেন {token}। আপনার পালা কাছে এলে বিজ্ঞপ্তি পাবেন।', 'queue_alert': 'সারি আপডেট হয়েছে! এখন চলছে: {current}\\nআপনার P104 টোকেন প্রায় {ahead} অবস্থান দূরে।', 'slots_left': '{n}টি স্লট বাকি', 'full': 'পূর্ণ'}, 'ta': {'name': 'தமிழ்', 'home': 'முகப்பு', 'register_nav': 'பதிவு', 'queue_nav': 'நேரடி வரிசை', 'status_nav': 'நிலை', 'hero_title': 'ஸ்மார்ட் கொள்முதல்,<br>புதுமை வேரூன்றும் இடம்', 'hero_desc': 'பயிரைப் பதிவு செய்து, நேரத்தை முன்பதிவு செய்து, டிஜிட்டல் டோக்கன் பெற்று, கொள்முதல் மற்றும் பணப்பரிவர்த்தனை நிலையை ஒரே இடத்தில் பார்க்கவும்.', 'book': 'ஸ்லாட்டை முன்பதிவு செய்க →', 'centre': '📍 கொள்முதல் மையம் — இன்று', 'current_token': 'தற்போதைய டோக்கன்', 'waiting': 'காத்திருக்கும் விவசாயிகள்: 6', 'centre_status': 'மைய நிலை:', 'open': '● திறந்துள்ளது', 'how_title': 'KisanGati எப்படி செயல்படுகிறது', 'how_desc': 'வெளிப்படையான வேளாண் கொள்முதலுக்கான டிஜிட்டல் நடைமுறை.', 'reg': '1. விவசாயி பதிவு', 'reg_desc': 'விவசாயி விவரங்கள், பயிர் மற்றும் எதிர்பார்க்கப்படும் அளவை ஆன்லைனில் பதிவு செய்யவும்.', 'slot': '2. ஸ்லாட் முன்பதிவு', 'slot_desc': 'கூட்டத்தில் காத்திருக்காமல் கிடைக்கும் கொள்முதல் நேரத்தை தேர்வு செய்யவும்.', 'token': '3. டிஜிட்டல் டோக்கன்', 'token_desc': 'டோக்கன் பெற்று வரிசையில் உங்கள் நிலையைப் பார்க்கவும்.', 'notify': '4. ஸ்மார்ட் அறிவிப்புகள்', 'notify_desc': 'உங்கள் முறை நெருங்கும்போது அறிவிப்பு பெறவும்.', 'proc': '5. கொள்முதல் கண்காணிப்பு', 'proc_desc': 'தரச் சோதனை, எடை மற்றும் கொள்முதல் முன்னேற்றத்தைப் பார்க்கவும்.', 'pay': '6. பணம் கண்காணிப்பு', 'pay_desc': 'எதிர்பார்க்கப்படும் தொகை மற்றும் பணப்பரிவர்த்தனை நிலையைப் பார்க்கவும்.', 'reg_title': 'விவசாயி பதிவு & ஸ்லாட் முன்பதிவு', 'reg_sub': 'டிஜிட்டல் டோக்கன் பெற உங்கள் விவரங்களை உள்ளிடவும்.', 'farmer_name': 'விவசாயி பெயர்', 'mobile': 'மொபைல் எண்', 'farmer_id': 'விவசாயி ID', 'crop': 'பயிர்', 'quantity': 'அளவு (குவிண்டால்)', 'available_slot': 'கிடைக்கும் ஸ்லாட்', 'submit': 'பதிவு செய்து டோக்கன் பெறுக', 'today_slots': 'இன்றைய ஸ்லாட்கள்', 'slots_help': 'ஸ்லாட்கள் விவசாயிகளின் வருகையைப் பகிர்ந்து கூட்டத்தைக் குறைக்க உதவுகின்றன.', 'live': '🔴 நேரடி வரிசை மேலாண்மை', 'live_sub': 'காத்திருக்காமல் உங்கள் வரிசை நிலையைப் பார்க்கவும்.', 'serving': 'தற்போது', 'next': 'அடுத்து:', 'sample': 'உங்கள் மாதிரி டோக்கன்', 'away': '6 இடங்கள் தூரம்', 'simulate': 'அடுத்த விவசாயியை உருவகப்படுத்து', 'status_title': '📦 கொள்முதல் & பணப்பரிவர்த்தனை நிலை', 'status_sub': 'முன்பதிவு முதல் பணம் வரை முழு வெளிப்படைத்தன்மை.', 'booking': 'முன்பதிவு', 'arrived': 'வந்தடைந்தது', 'queue': 'வரிசை', 'quality': 'தரச் சோதனை', 'weighing': 'எடை', 'procurement': 'கொள்முதல்', 'payment_processing': 'பணம் செயலாக்கம்', 'payment_received': 'பணம் பெறப்பட்டது', 'completed': 'முடிந்தது ✓', 'processing': 'செயலாக்கத்தில்', 'recent': 'சமீபத்திய பதிவுகள்', 'recent_sub': 'டெமோ தரவு SQLite-ல் சேமிக்கப்பட்டுள்ளது.', 'status': 'நிலை', 'no_reg': 'இன்னும் பதிவுகள் இல்லை.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 டெமோ | வேளாண் கொள்முதல் தானியக்கம்', 'success': 'பதிவு வெற்றி! உங்கள் டிஜிட்டல் டோக்கன் {token}. உங்கள் முறை நெருங்கும்போது அறிவிப்பு வரும்.', 'queue_alert': 'வரிசை புதுப்பிக்கப்பட்டது! தற்போது: {current}\\nஉங்கள் P104 டோக்கன் சுமார் {ahead} இடங்கள் தூரத்தில் உள்ளது.', 'slots_left': '{n} ஸ்லாட்கள் மீதம்', 'full': 'நிரம்பியது'},
'as': {'name': 'অসমীয়া', 'home': 'হোম', 'register_nav': 'পঞ্জীয়ন', 'queue_nav': 'লাইভ শাৰী', 'status_nav': 'স্থিতি', 'hero_title': 'স্মাৰ্ট ক্ৰয়,<br>য\'ত উদ্ভাৱনে শিপা মেলে', 'hero_desc': 'আপোনাৰ শস্য পঞ্জীয়ন কৰক, সময়ৰ স্লট বুক কৰক, ডিজিটেল টোকেন লওক আৰু ক্ৰয় আৰু পেমেণ্টৰ অৱস্থা একে ঠাইতে চাওক।', 'book': 'স্লট বুক কৰক →', 'centre': '📍 ক্ৰয় কেন্দ্ৰ — আজি', 'current_token': 'বৰ্তমান টোকেন', 'waiting': 'আনুমানিক অপেক্ষাৰত কৃষক: 6', 'centre_status': 'কেন্দ্ৰৰ অৱস্থা:', 'open': '● খোলা', 'how_title': 'KisanGati কেনেকৈ কাম কৰে', 'how_desc': 'স্বচ্ছ কৃষি ক্ৰয়ৰ বাবে ডিজিটেল ব্যৱস্থা।', 'reg': '1. কৃষক পঞ্জীয়ন', 'reg_desc': 'কৃষকৰ তথ্য, শস্য আৰু আনুমানিক পৰিমাণ অনলাইনত পঞ্জীয়ন কৰক।', 'slot': '2. স্লট বুকিং', 'slot_desc': 'ভিৰত অপেক্ষা কৰাৰ সলনি উপলব্ধ ক্ৰয় স্লট বাছনি কৰক।', 'token': '3. ডিজিটেল টোকেন', 'token_desc': 'টোকেন লাভ কৰক আৰু শাৰীত আপোনাৰ অৱস্থান চাওক।', 'notify': '4. স্মাৰ্ট জাননী', 'notify_desc': 'আপোনাৰ পালি ওচৰ চাপিলে জাননী লাভ কৰক।', 'proc': '5. ক্ৰয় অনুসৰণ', 'proc_desc': 'গুণগত পৰীক্ষা, ওজন আৰু ক্ৰয়ৰ অগ্ৰগতি চাওক।', 'pay': '6. পেমেণ্ট অনুসৰণ', 'pay_desc': 'আশা কৰা ধন আৰু পেমেণ্টৰ অৱস্থা চাওক।', 'reg_title': 'কৃষক পঞ্জীয়ন আৰু স্লট বুকিং', 'reg_sub': 'ডিজিটেল টোকেন লাভ কৰিবলৈ আপোনাৰ তথ্য দিয়ক।', 'farmer_name': 'কৃষকৰ নাম', 'mobile': 'মোবাইল নম্বৰ', 'farmer_id': 'কৃষক ID', 'crop': 'শস্য', 'quantity': 'পৰিমাণ (কুইণ্টল)', 'available_slot': 'উপলব্ধ স্লট', 'submit': 'পঞ্জীয়ন কৰক আৰু টোকেন লওক', 'today_slots': 'আজিৰ স্লট', 'slots_help': 'স্লটে কৃষকৰ আগমন ভাগ কৰি ভিৰ কম কৰাত সহায় কৰে।', 'live': '🔴 লাইভ শাৰী ব্যৱস্থাপনা', 'live_sub': 'অপ্ৰয়োজনীয়ভাৱে অপেক্ষা নকৰি আপোনাৰ শাৰীৰ অৱস্থান চাওক।', 'serving': 'এতিয়া চলি আছে', 'next': 'পৰৱৰ্তী:', 'sample': 'আপোনাৰ নমুনা টোকেন', 'away': '6 স্থান দূৰত', 'simulate': 'পৰৱৰ্তী কৃষকৰ অনুকৰণ', 'status_title': '📦 ক্ৰয় আৰু পেমেণ্টৰ অৱস্থা', 'status_sub': 'বুকিঙৰ পৰা পেমেণ্টলৈ সম্পূৰ্ণ স্বচ্ছতা।', 'booking': 'বুকিং', 'arrived': 'উপস্থিত', 'queue': 'শাৰী', 'quality': 'গুণগত পৰীক্ষা', 'weighing': 'ওজন', 'procurement': 'ক্ৰয়', 'payment_processing': 'পেমেণ্ট প্ৰক্ৰিয়াধীন', 'payment_received': 'পেমেণ্ট লাভ কৰা হৈছে', 'completed': 'সম্পূৰ্ণ ✓', 'processing': 'প্ৰক্ৰিয়াধীন', 'recent': 'শেহতীয়া পঞ্জীয়ন', 'recent_sub': 'ডেমো তথ্য SQLite-ত সংৰক্ষিত।', 'status': 'অৱস্থা', 'no_reg': 'এতিয়াও কোনো পঞ্জীয়ন নাই।', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 ডেমো | কৃষি ক্ৰয় স্বয়ংক্ৰিয়কৰণ', 'success': 'পঞ্জীয়ন সফল! আপোনাৰ ডিজিটেল টোকেন {token}। আপোনাৰ পালি ওচৰ চাপিলে জাননী লাভ কৰিব।', 'queue_alert': 'শাৰী আপডেট হৈছে! এতিয়া চলি আছে: {current}\\nআপোনাৰ P104 টোকেন প্ৰায় {ahead} স্থান দূৰত।', 'slots_left': '{n}টা স্লট বাকী', 'full': 'পূৰ্ণ'},
'te': {'name': 'తెలుగు', 'home': 'హోమ్', 'register_nav': 'నమోదు', 'queue_nav': 'లైవ్ క్యూ', 'status_nav': 'స్థితి', 'hero_title': 'స్మార్ట్ కొనుగోలు,<br>ఎక్కడ ఆవిష్కరణ వేళ్లూనుకుంటుందో', 'hero_desc': 'మీ పంటను నమోదు చేయండి, సమయ స్లాట్ బుక్ చేసుకోండి, డిజిటల్ టోకెన్ పొందండి మరియు కొనుగోలు, చెల్లింపు స్థితిని ఒకే చోట చూడండి.', 'book': 'స్లాట్ బుక్ చేయండి →', 'centre': '📍 కొనుగోలు కేంద్రం — ఈరోజు', 'current_token': 'ప్రస్తుతం సేవలందిస్తున్న టోకెన్', 'waiting': 'అంచనా వేచి ఉన్న రైతులు: 6', 'centre_status': 'కేంద్ర స్థితి:', 'open': '● తెరిచి ఉంది', 'how_title': 'KisanGati ఎలా పనిచేస్తుంది', 'how_desc': 'పారదర్శక వ్యవసాయ కొనుగోలు కోసం డిజిటల్ విధానం.', 'reg': '1. రైతు నమోదు', 'reg_desc': 'రైతు వివరాలు, పంట మరియు అంచనా పరిమాణాన్ని ఆన్\u200cలైన్\u200cలో నమోదు చేయండి.', 'slot': '2. స్లాట్ బుకింగ్', 'slot_desc': 'పెద్ద క్యూలో వేచి ఉండకుండా అందుబాటులో ఉన్న కొనుగోలు స్లాట్ ఎంచుకోండి.', 'token': '3. డిజిటల్ టోకెన్', 'token_desc': 'టోకెన్ పొందండి మరియు క్యూలో మీ స్థానాన్ని చూడండి.', 'notify': '4. స్మార్ట్ నోటిఫికేషన్లు', 'notify_desc': 'మీ వంతు దగ్గరపడినప్పుడు సమాచారం పొందండి.', 'proc': '5. కొనుగోలు ట్రాకింగ్', 'proc_desc': 'నాణ్యత తనిఖీ, బరువు మరియు కొనుగోలు పురోగతిని చూడండి.', 'pay': '6. చెల్లింపు ట్రాకింగ్', 'pay_desc': 'అంచనా మొత్తం మరియు చెల్లింపు స్థితిని చూడండి.', 'reg_title': 'రైతు నమోదు & స్లాట్ బుకింగ్', 'reg_sub': 'డిజిటల్ టోకెన్ పొందడానికి మీ వివరాలు నమోదు చేయండి.', 'farmer_name': 'రైతు పేరు', 'mobile': 'మొబైల్ నంబర్', 'farmer_id': 'రైతు ID', 'crop': 'పంట', 'quantity': 'పరిమాణం (క్వింటాళ్లు)', 'available_slot': 'అందుబాటులో ఉన్న స్లాట్', 'submit': 'నమోదు చేసి టోకెన్ పొందండి', 'today_slots': 'ఈరోజు స్లాట్లు', 'slots_help': 'స్లాట్లు రైతుల రాకను విభజించి రద్దీని తగ్గిస్తాయి.', 'live': '🔴 లైవ్ క్యూ నిర్వహణ', 'live_sub': 'అవసరం లేకుండా వేచి ఉండకుండా మీ క్యూ స్థానాన్ని చూడండి.', 'serving': 'ప్రస్తుతం', 'next': 'తర్వాత:', 'sample': 'మీ నమూనా టోకెన్', 'away': '6 స్థానాల దూరంలో', 'simulate': 'తదుపరి రైతును అనుకరించండి', 'status_title': '📦 కొనుగోలు & చెల్లింపు స్థితి', 'status_sub': 'బుకింగ్ నుంచి చెల్లింపు వరకు పూర్తి పారదర్శకత.', 'booking': 'బుకింగ్', 'arrived': 'చేరుకున్నారు', 'queue': 'క్యూ', 'quality': 'నాణ్యత తనిఖీ', 'weighing': 'బరువు', 'procurement': 'కొనుగోలు', 'payment_processing': 'చెల్లింపు ప్రాసెసింగ్', 'payment_received': 'చెల్లింపు అందింది', 'completed': 'పూర్తయింది ✓', 'processing': 'ప్రాసెసింగ్\u200cలో ఉంది', 'recent': 'ఇటీవలి నమోదులు', 'recent_sub': 'డెమో డేటా SQLiteలో నిల్వ చేయబడింది.', 'status': 'స్థితి', 'no_reg': 'ఇంకా నమోదులు లేవు.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 డెమో | వ్యవసాయ కొనుగోలు ఆటోమేషన్', 'success': 'నమోదు విజయవంతం! మీ డిజిటల్ టోకెన్ {token}. మీ వంతు దగ్గరపడినప్పుడు సమాచారం అందుతుంది.', 'queue_alert': 'క్యూ నవీకరించబడింది! ప్రస్తుతం: {current}\\nమీ P104 టోకెన్ సుమారు {ahead} స్థానాల దూరంలో ఉంది.', 'slots_left': '{n} స్లాట్లు మిగిలి ఉన్నాయి', 'full': 'పూర్తి'},
'mr': {'name': 'मराठी', 'home': 'मुख्यपृष्ठ', 'register_nav': 'नोंदणी', 'queue_nav': 'लाइव्ह रांग', 'status_nav': 'स्थिती', 'hero_title': 'स्मार्ट खरेदी,<br>जिथे नवकल्पना रुजते', 'hero_desc': 'तुमचे पीक नोंदवा, वेळेचा स्लॉट बुक करा, डिजिटल टोकन मिळवा आणि खरेदी व पेमेंटची स्थिती एकाच ठिकाणी पाहा.', 'book': 'स्लॉट बुक करा →', 'centre': '📍 खरेदी केंद्र — आज', 'current_token': 'सध्या सुरू असलेले टोकन', 'waiting': 'अंदाजे प्रतीक्षेत असलेले शेतकरी: 6', 'centre_status': 'केंद्राची स्थिती:', 'open': '● खुले', 'how_title': 'KisanGati कसे काम करते', 'how_desc': 'पारदर्शक कृषी खरेदीसाठी डिजिटल प्रक्रिया.', 'reg': '1. शेतकरी नोंदणी', 'reg_desc': 'शेतकऱ्याची माहिती, पीक आणि अपेक्षित प्रमाण ऑनलाइन नोंदवा.', 'slot': '2. स्लॉट बुकिंग', 'slot_desc': 'मोठ्या गर्दीत थांबण्याऐवजी उपलब्ध खरेदी स्लॉट निवडा.', 'token': '3. डिजिटल टोकन', 'token_desc': 'टोकन मिळवा आणि रांगेतील तुमचे स्थान पाहा.', 'notify': '4. स्मार्ट सूचना', 'notify_desc': 'तुमची पाळी जवळ आल्यावर सूचना मिळवा.', 'proc': '5. खरेदी ट्रॅकिंग', 'proc_desc': 'गुणवत्ता तपासणी, वजन आणि खरेदीची प्रगती पाहा.', 'pay': '6. पेमेंट ट्रॅकिंग', 'pay_desc': 'अपेक्षित रक्कम आणि पेमेंटची स्थिती पाहा.', 'reg_title': 'शेतकरी नोंदणी आणि स्लॉट बुकिंग', 'reg_sub': 'डिजिटल टोकन मिळवण्यासाठी तुमची माहिती भरा.', 'farmer_name': 'शेतकऱ्याचे नाव', 'mobile': 'मोबाईल नंबर', 'farmer_id': 'शेतकरी ID', 'crop': 'पीक', 'quantity': 'प्रमाण (क्विंटल)', 'available_slot': 'उपलब्ध स्लॉट', 'submit': 'नोंदणी करा आणि टोकन मिळवा', 'today_slots': 'आजचे स्लॉट', 'slots_help': 'स्लॉट शेतकऱ्यांचे आगमन विभागून गर्दी कमी करण्यास मदत करतात.', 'live': '🔴 लाइव्ह रांग व्यवस्थापन', 'live_sub': 'विनाकारण थांबण्याऐवजी तुमचे रांगेतील स्थान पाहा.', 'serving': 'सध्या सुरू', 'next': 'पुढील:', 'sample': 'तुमचे नमुना टोकन', 'away': '6 स्थानांवर', 'simulate': 'पुढील शेतकऱ्याचे सिम्युलेशन', 'status_title': '📦 खरेदी आणि पेमेंट स्थिती', 'status_sub': 'बुकिंगपासून पेमेंटपर्यंत पूर्ण पारदर्शकता.', 'booking': 'बुकिंग', 'arrived': 'पोहोचले', 'queue': 'रांग', 'quality': 'गुणवत्ता तपासणी', 'weighing': 'वजन', 'procurement': 'खरेदी', 'payment_processing': 'पेमेंट प्रक्रियेत', 'payment_received': 'पेमेंट प्राप्त', 'completed': 'पूर्ण ✓', 'processing': 'प्रक्रियेत', 'recent': 'अलीकडील नोंदणी', 'recent_sub': 'डेमो डेटा SQLite मध्ये साठवला आहे.', 'status': 'स्थिती', 'no_reg': 'अद्याप कोणतीही नोंदणी नाही.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 डेमो | कृषी खरेदी स्वयंचलितकरण', 'success': 'नोंदणी यशस्वी! तुमचे डिजिटल टोकन {token}. तुमची पाळी जवळ आल्यावर सूचना मिळेल.', 'queue_alert': 'रांग अपडेट झाली! सध्या: {current}\\nतुमचे P104 टोकन अंदाजे {ahead} स्थानांवर आहे.', 'slots_left': '{n} स्लॉट बाकी', 'full': 'पूर्ण'},
'gu': {'name': 'ગુજરાતી', 'home': 'હોમ', 'register_nav': 'નોંધણી', 'queue_nav': 'લાઇવ કતાર', 'status_nav': 'સ્થિતિ', 'hero_title': 'સ્માર્ટ ખરીદી,<br>જ્યાં નવીનતા મૂળિયાં જમાવે છે', 'hero_desc': 'તમારો પાક નોંધાવો, સમયનો સ્લોટ બુક કરો, ડિજિટલ ટોકન મેળવો અને ખરીદી તથા ચુકવણીની સ્થિતિ એક જ જગ્યાએ જુઓ.', 'book': 'સ્લોટ બુક કરો →', 'centre': '📍 ખરીદી કેન્દ્ર — આજે', 'current_token': 'હાલમાં સેવા આપતો ટોકન', 'waiting': 'અંદાજિત રાહ જોતા ખેડૂતો: 6', 'centre_status': 'કેન્દ્રની સ્થિતિ:', 'open': '● ખુલ્લું', 'how_title': 'KisanGati કેવી રીતે કામ કરે છે', 'how_desc': 'પારદર્શક કૃષિ ખરીદી માટે ડિજિટલ પ્રક્રિયા.', 'reg': '1. ખેડૂત નોંધણી', 'reg_desc': 'ખેડૂતની વિગતો, પાક અને અપેક્ષિત જથ્થો ઓનલાઈન નોંધાવો.', 'slot': '2. સ્લોટ બુકિંગ', 'slot_desc': 'મોટી ભીડમાં રાહ જોવાને બદલે ઉપલબ્ધ ખરીદી સ્લોટ પસંદ કરો.', 'token': '3. ડિજિટલ ટોકન', 'token_desc': 'ટોકન મેળવો અને કતારમાં તમારું સ્થાન જુઓ.', 'notify': '4. સ્માર્ટ સૂચનાઓ', 'notify_desc': 'તમારો વારો નજીક આવે ત્યારે સૂચના મેળવો.', 'proc': '5. ખરીદી ટ્રેકિંગ', 'proc_desc': 'ગુણવત્તા તપાસ, વજન અને ખરીદીની પ્રગતિ જુઓ.', 'pay': '6. ચુકવણી ટ્રેકિંગ', 'pay_desc': 'અપેક્ષિત રકમ અને ચુકવણીની સ્થિતિ જુઓ.', 'reg_title': 'ખેડૂત નોંધણી અને સ્લોટ બુકિંગ', 'reg_sub': 'ડિજિટલ ટોકન મેળવવા તમારી વિગતો દાખલ કરો.', 'farmer_name': 'ખેડૂતનું નામ', 'mobile': 'મોબાઇલ નંબર', 'farmer_id': 'ખેડૂત ID', 'crop': 'પાક', 'quantity': 'જથ્થો (ક્વિન્ટલ)', 'available_slot': 'ઉપલબ્ધ સ્લોટ', 'submit': 'નોંધણી કરો અને ટોકન મેળવો', 'today_slots': 'આજના સ્લોટ', 'slots_help': 'સ્લોટ ખેડૂતોના આગમનને વહેંચે છે અને ભીડ ઘટાડે છે.', 'live': '🔴 લાઇવ કતાર વ્યવસ્થાપન', 'live_sub': 'અંધાધૂંધ રાહ જોયા વગર તમારી કતારની સ્થિતિ જુઓ.', 'serving': 'હાલમાં', 'next': 'આગળ:', 'sample': 'તમારો નમૂના ટોકન', 'away': '6 સ્થાન દૂર', 'simulate': 'આગળના ખેડૂતનું સિમ્યુલેશન', 'status_title': '📦 ખરીદી અને ચુકવણીની સ્થિતિ', 'status_sub': 'બુકિંગથી ચુકવણી સુધી સંપૂર્ણ પારદર્શિતા.', 'booking': 'બુકિંગ', 'arrived': 'પહોંચ્યા', 'queue': 'કતાર', 'quality': 'ગુણવત્તા તપાસ', 'weighing': 'વજન', 'procurement': 'ખરીદી', 'payment_processing': 'ચુકવણી પ્રક્રિયામાં', 'payment_received': 'ચુકવણી પ્રાપ્ત', 'completed': 'પૂર્ણ ✓', 'processing': 'પ્રક્રિયામાં', 'recent': 'તાજેતરની નોંધણીઓ', 'recent_sub': 'ડેમો ડેટા SQLiteમાં સંગ્રહિત છે.', 'status': 'સ્થિતિ', 'no_reg': 'હજુ કોઈ નોંધણી નથી.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 ડેમો | કૃષિ ખરીદી ઓટોમેશન', 'success': 'નોંધણી સફળ! તમારું ડિજિટલ ટોકન {token}. તમારો વારો નજીક આવે ત્યારે સૂચના મળશે.', 'queue_alert': 'કતાર અપડેટ થઈ! હાલમાં: {current}\\nતમારું P104 ટોકન લગભગ {ahead} સ્થાન દૂર છે.', 'slots_left': '{n} સ્લોટ બાકી', 'full': 'ભરેલું'},
'kn': {'name': 'ಕನ್ನಡ', 'home': 'ಮುಖಪುಟ', 'register_nav': 'ನೋಂದಣಿ', 'queue_nav': 'ಲೈವ್ ಸರದಿ', 'status_nav': 'ಸ್ಥಿತಿ', 'hero_title': 'ಸ್ಮಾರ್ಟ್ ಖರೀದಿ,<br>ಎಲ್ಲಿ ನಾವೀನ್ಯತೆ ಬೇರುಬಿಡುತ್ತದೆಯೋ', 'hero_desc': 'ನಿಮ್ಮ ಬೆಳೆಯನ್ನು ನೋಂದಾಯಿಸಿ, ಸಮಯದ ಸ್ಲಾಟ್ ಬುಕ್ ಮಾಡಿ, ಡಿಜಿಟಲ್ ಟೋಕನ್ ಪಡೆಯಿರಿ ಮತ್ತು ಖರೀದಿ ಹಾಗೂ ಪಾವತಿ ಸ್ಥಿತಿಯನ್ನು ಒಂದೇ ಸ್ಥಳದಲ್ಲಿ ನೋಡಿ.', 'book': 'ಸ್ಲಾಟ್ ಬುಕ್ ಮಾಡಿ →', 'centre': '📍 ಖರೀದಿ ಕೇಂದ್ರ — ಇಂದು', 'current_token': 'ಪ್ರಸ್ತುತ ಸೇವೆಯಲ್ಲಿರುವ ಟೋಕನ್', 'waiting': 'ಅಂದಾಜು ಕಾಯುತ್ತಿರುವ ರೈತರು: 6', 'centre_status': 'ಕೇಂದ್ರದ ಸ್ಥಿತಿ:', 'open': '● ತೆರೆದಿದೆ', 'how_title': 'KisanGati ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ', 'how_desc': 'ಪಾರದರ್ಶಕ ಕೃಷಿ ಖರೀದಿಗಾಗಿ ಡಿಜಿಟಲ್ ಪ್ರಕ್ರಿಯೆ.', 'reg': '1. ರೈತರ ನೋಂದಣಿ', 'reg_desc': 'ರೈತರ ವಿವರಗಳು, ಬೆಳೆ ಮತ್ತು ನಿರೀಕ್ಷಿತ ಪ್ರಮಾಣವನ್ನು ಆನ್\u200cಲೈನ್\u200cನಲ್ಲಿ ನೋಂದಾಯಿಸಿ.', 'slot': '2. ಸ್ಲಾಟ್ ಬುಕ್ಕಿಂಗ್', 'slot_desc': 'ದೊಡ್ಡ ಗುಂಪಿನಲ್ಲಿ ಕಾಯುವುದಕ್ಕಿಂತ ಲಭ್ಯವಿರುವ ಖರೀದಿ ಸ್ಲಾಟ್ ಆಯ್ಕೆಮಾಡಿ.', 'token': '3. ಡಿಜಿಟಲ್ ಟೋಕನ್', 'token_desc': 'ಟೋಕನ್ ಪಡೆದು ಸರದಿಯಲ್ಲಿ ನಿಮ್ಮ ಸ್ಥಾನವನ್ನು ನೋಡಿ.', 'notify': '4. ಸ್ಮಾರ್ಟ್ ಅಧಿಸೂಚನೆಗಳು', 'notify_desc': 'ನಿಮ್ಮ ಸರದಿ ಹತ್ತಿರ ಬಂದಾಗ ಅಧಿಸೂಚನೆ ಪಡೆಯಿರಿ.', 'proc': '5. ಖರೀದಿ ಟ್ರ್ಯಾಕಿಂಗ್', 'proc_desc': 'ಗುಣಮಟ್ಟ ಪರಿಶೀಲನೆ, ತೂಕ ಮತ್ತು ಖರೀದಿ ಪ್ರಗತಿಯನ್ನು ನೋಡಿ.', 'pay': '6. ಪಾವತಿ ಟ್ರ್ಯಾಕಿಂಗ್', 'pay_desc': 'ನಿರೀಕ್ಷಿತ ಮೊತ್ತ ಮತ್ತು ಪಾವತಿಯ ಸ್ಥಿತಿಯನ್ನು ನೋಡಿ.', 'reg_title': 'ರೈತರ ನೋಂದಣಿ ಮತ್ತು ಸ್ಲಾಟ್ ಬುಕ್ಕಿಂಗ್', 'reg_sub': 'ಡಿಜಿಟಲ್ ಟೋಕನ್ ಪಡೆಯಲು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ.', 'farmer_name': 'ರೈತರ ಹೆಸರು', 'mobile': 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ', 'farmer_id': 'ರೈತರ ID', 'crop': 'ಬೆಳೆ', 'quantity': 'ಪ್ರಮಾಣ (ಕ್ವಿಂಟಲ್)', 'available_slot': 'ಲಭ್ಯವಿರುವ ಸ್ಲಾಟ್', 'submit': 'ನೋಂದಣಿ ಮಾಡಿ ಟೋಕನ್ ಪಡೆಯಿರಿ', 'today_slots': 'ಇಂದಿನ ಸ್ಲಾಟ್\u200cಗಳು', 'slots_help': 'ಸ್ಲಾಟ್\u200cಗಳು ರೈತರ ಆಗಮನವನ್ನು ಹಂಚಿ ಜನಸಂದಣಿಯನ್ನು ಕಡಿಮೆ ಮಾಡುತ್ತವೆ.', 'live': '🔴 ಲೈವ್ ಸರದಿ ನಿರ್ವಹಣೆ', 'live_sub': 'ಅಗತ್ಯವಿಲ್ಲದೆ ಕಾಯದೆ ನಿಮ್ಮ ಸರದಿ ಸ್ಥಾನವನ್ನು ನೋಡಿ.', 'serving': 'ಪ್ರಸ್ತುತ', 'next': 'ಮುಂದೆ:', 'sample': 'ನಿಮ್ಮ ಮಾದರಿ ಟೋಕನ್', 'away': '6 ಸ್ಥಾನ ದೂರ', 'simulate': 'ಮುಂದಿನ ರೈತನ ಸಿಮ್ಯುಲೇಶನ್', 'status_title': '📦 ಖರೀದಿ ಮತ್ತು ಪಾವತಿ ಸ್ಥಿತಿ', 'status_sub': 'ಬುಕ್ಕಿಂಗ್\u200cನಿಂದ ಪಾವತಿವರೆಗೆ ಸಂಪೂರ್ಣ ಪಾರದರ್ಶಕತೆ.', 'booking': 'ಬುಕ್ಕಿಂಗ್', 'arrived': 'ಆಗಮಿಸಲಾಗಿದೆ', 'queue': 'ಸರದಿ', 'quality': 'ಗುಣಮಟ್ಟ ಪರಿಶೀಲನೆ', 'weighing': 'ತೂಕ', 'procurement': 'ಖರೀದಿ', 'payment_processing': 'ಪಾವತಿ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ', 'payment_received': 'ಪಾವತಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ', 'completed': 'ಪೂರ್ಣ ✓', 'processing': 'ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ', 'recent': 'ಇತ್ತೀಚಿನ ನೋಂದಣಿಗಳು', 'recent_sub': 'ಡೆಮೊ ಡೇಟಾವನ್ನು SQLite ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಲಾಗಿದೆ.', 'status': 'ಸ್ಥಿತಿ', 'no_reg': 'ಇನ್ನೂ ಯಾವುದೇ ನೋಂದಣಿಗಳಿಲ್ಲ.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 ಡೆಮೊ | ಕೃಷಿ ಖರೀದಿ ಸ್ವಯಂಚಾಲನೆ', 'success': 'ನೋಂದಣಿ ಯಶಸ್ವಿ! ನಿಮ್ಮ ಡಿಜಿಟಲ್ ಟೋಕನ್ {token}. ನಿಮ್ಮ ಸರದಿ ಹತ್ತಿರ ಬಂದಾಗ ಅಧಿಸೂಚನೆ ಸಿಗುತ್ತದೆ.', 'queue_alert': 'ಸರದಿ ನವೀಕರಿಸಲಾಗಿದೆ! ಪ್ರಸ್ತುತ: {current}\\nನಿಮ್ಮ P104 ಟೋಕನ್ ಸುಮಾರು {ahead} ಸ್ಥಾನ ದೂರದಲ್ಲಿದೆ.', 'slots_left': '{n} ಸ್ಲಾಟ್\u200cಗಳು ಉಳಿದಿವೆ', 'full': 'ಪೂರ್ಣ'},
'ml': {'name': 'മലയാളം', 'home': 'ഹോം', 'register_nav': 'രജിസ്റ്റർ', 'queue_nav': 'ലൈവ് ക്യൂ', 'status_nav': 'സ്ഥിതി', 'hero_title': 'സ്മാർട്ട് വാങ്ങൽ,<br>നവീനത വേരൂന്നുന്നിടം', 'hero_desc': 'നിങ്ങളുടെ വിള രജിസ്റ്റർ ചെയ്യുക, സമയ സ്ലോട്ട് ബുക്ക് ചെയ്യുക, ഡിജിറ്റൽ ടോക്കൺ നേടുക, വാങ്ങലിന്റെയും പണമടയ്ക്കലിന്റെയും സ്ഥിതി ഒരിടത്ത് കാണുക.', 'book': 'സ്ലോട്ട് ബുക്ക് ചെയ്യുക →', 'centre': '📍 വാങ്ങൽ കേന്ദ്രം — ഇന്ന്', 'current_token': 'നിലവിൽ സേവനം ലഭിക്കുന്ന ടോക്കൺ', 'waiting': 'കാത്തിരിക്കുന്ന കർഷകർ: 6', 'centre_status': 'കേന്ദ്രത്തിന്റെ സ്ഥിതി:', 'open': '● തുറന്നിരിക്കുന്നു', 'how_title': 'KisanGati എങ്ങനെ പ്രവർത്തിക്കുന്നു', 'how_desc': 'സുതാര്യമായ കാർഷിക വാങ്ങലിനുള്ള ഡിജിറ്റൽ സംവിധാനം.', 'reg': '1. കർഷക രജിസ്ട്രേഷൻ', 'reg_desc': 'കർഷക വിവരങ്ങൾ, വിള, പ്രതീക്ഷിക്കുന്ന അളവ് എന്നിവ ഓൺലൈനായി രജിസ്റ്റർ ചെയ്യുക.', 'slot': '2. സ്ലോട്ട് ബുക്കിംഗ്', 'slot_desc': 'വലിയ തിരക്കിൽ കാത്തിരിക്കാതെ ലഭ്യമായ വാങ്ങൽ സ്ലോട്ട് തിരഞ്ഞെടുക്കുക.', 'token': '3. ഡിജിറ്റൽ ടോക്കൺ', 'token_desc': 'ടോക്കൺ നേടി ക്യൂവിലെ നിങ്ങളുടെ സ്ഥാനം കാണുക.', 'notify': '4. സ്മാർട്ട് അറിയിപ്പുകൾ', 'notify_desc': 'നിങ്ങളുടെ ഊഴം അടുത്തെത്തുമ്പോൾ അറിയിപ്പ് നേടുക.', 'proc': '5. വാങ്ങൽ ട്രാക്കിംഗ്', 'proc_desc': 'ഗുണനിലവാര പരിശോധന, തൂക്കം, വാങ്ങൽ പുരോഗതി എന്നിവ കാണുക.', 'pay': '6. പേയ്മെന്റ് ട്രാക്കിംഗ്', 'pay_desc': 'പ്രതീക്ഷിക്കുന്ന തുകയും പേയ്മെന്റിന്റെ നിലയും കാണുക.', 'reg_title': 'കർഷക രജിസ്ട്രേഷനും സ്ലോട്ട് ബുക്കിംഗും', 'reg_sub': 'ഡിജിറ്റൽ ടോക്കൺ ലഭിക്കാൻ നിങ്ങളുടെ വിവരങ്ങൾ നൽകുക.', 'farmer_name': 'കർഷകന്റെ പേര്', 'mobile': 'മൊബൈൽ നമ്പർ', 'farmer_id': 'കർഷക ID', 'crop': 'വിള', 'quantity': 'അളവ് (ക്വിന്റൽ)', 'available_slot': 'ലഭ്യമായ സ്ലോട്ട്', 'submit': 'രജിസ്റ്റർ ചെയ്ത് ടോക്കൺ നേടുക', 'today_slots': 'ഇന്നത്തെ സ്ലോട്ടുകൾ', 'slots_help': 'സ്ലോട്ടുകൾ കർഷകരുടെ വരവ് വിഭജിച്ച് തിരക്ക് കുറയ്ക്കാൻ സഹായിക്കുന്നു.', 'live': '🔴 ലൈവ് ക്യൂ മാനേജ്മെന്റ്', 'live_sub': 'വെറുതെ കാത്തിരിക്കാതെ നിങ്ങളുടെ ക്യൂ സ്ഥാനം കാണുക.', 'serving': 'ഇപ്പോൾ', 'next': 'അടുത്തത്:', 'sample': 'നിങ്ങളുടെ മാതൃക ടോക്കൺ', 'away': '6 സ്ഥാനങ്ങൾ അകലെ', 'simulate': 'അടുത്ത കർഷകനെ സിമുലേറ്റ് ചെയ്യുക', 'status_title': '📦 വാങ്ങലിന്റെയും പേയ്മെന്റിന്റെയും സ്ഥിതി', 'status_sub': 'ബുക്കിംഗ് മുതൽ പേയ്മെന്റ് വരെ പൂർണ്ണ സുതാര്യത.', 'booking': 'ബുക്കിംഗ്', 'arrived': 'എത്തി', 'queue': 'ക്യൂ', 'quality': 'ഗുണനിലവാര പരിശോധന', 'weighing': 'തൂക്കം', 'procurement': 'വാങ്ങൽ', 'payment_processing': 'പേയ്മെന്റ് പ്രോസസ്സിംഗ്', 'payment_received': 'പേയ്മെന്റ് ലഭിച്ചു', 'completed': 'പൂർത്തിയായി ✓', 'processing': 'പ്രോസസ്സിംഗിൽ', 'recent': 'സമീപകാല രജിസ്ട്രേഷനുകൾ', 'recent_sub': 'ഡെമോ ഡാറ്റ SQLite-ൽ സൂക്ഷിച്ചിരിക്കുന്നു.', 'status': 'സ്ഥിതി', 'no_reg': 'ഇതുവരെ രജിസ്ട്രേഷനുകളില്ല.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 ഡെമോ | കാർഷിക വാങ്ങൽ ഓട്ടോമേഷൻ', 'success': 'രജിസ്ട്രേഷൻ വിജയകരം! നിങ്ങളുടെ ഡിജിറ്റൽ ടോക്കൺ {token}. നിങ്ങളുടെ ഊഴം അടുത്തെത്തുമ്പോൾ അറിയിപ്പ് ലഭിക്കും.', 'queue_alert': 'ക്യൂ അപ്ഡേറ്റ് ചെയ്തു! ഇപ്പോൾ: {current}\\nനിങ്ങളുടെ P104 ടോക്കൺ ഏകദേശം {ahead} സ്ഥാനങ്ങൾ അകലെയാണ്.', 'slots_left': '{n} സ്ലോട്ടുകൾ ബാക്കി', 'full': 'നിറഞ്ഞു'},
'or': {'name': 'ଓଡ଼ିଆ', 'home': 'ମୁଖ୍ୟପୃଷ୍ଠା', 'register_nav': 'ପଞ୍ଜୀକରଣ', 'queue_nav': 'ଲାଇଭ୍ ଧାଡ଼ି', 'status_nav': 'ସ୍ଥିତି', 'hero_title': 'ସ୍ମାର୍ଟ କ୍ରୟ,<br>ଯେଉଁଠାରେ ନବସୃଜନ ମୂଳ ଧରେ', 'hero_desc': 'ଆପଣଙ୍କ ଫସଲ ପଞ୍ଜୀକରଣ କରନ୍ତୁ, ସମୟ ସ୍ଲଟ୍ ବୁକ୍ କରନ୍ତୁ, ଡିଜିଟାଲ୍ ଟୋକେନ୍ ପାଆନ୍ତୁ ଏବଂ କ୍ରୟ ଓ ପେମେଣ୍ଟ ସ୍ଥିତି ଗୋଟିଏ ସ୍ଥାନରେ ଦେଖନ୍ତୁ।', 'book': 'ସ୍ଲଟ୍ ବୁକ୍ କରନ୍ତୁ →', 'centre': '📍 କ୍ରୟ କେନ୍ଦ୍ର — ଆଜି', 'current_token': 'ବର୍ତ୍ତମାନ ସେବା ଦିଆଯାଉଥିବା ଟୋକେନ୍', 'waiting': 'ଆନୁମାନିକ ଅପେକ୍ଷାରତ ଚାଷୀ: 6', 'centre_status': 'କେନ୍ଦ୍ରର ସ୍ଥିତି:', 'open': '● ଖୋଲା', 'how_title': 'KisanGati କିପରି କାମ କରେ', 'how_desc': 'ସ୍ୱଚ୍ଛ କୃଷି କ୍ରୟ ପାଇଁ ଡିଜିଟାଲ୍ ପ୍ରକ୍ରିୟା।', 'reg': '1. ଚାଷୀ ପଞ୍ଜୀକରଣ', 'reg_desc': 'ଚାଷୀଙ୍କ ବିବରଣୀ, ଫସଲ ଏବଂ ଆଶା କରାଯାଉଥିବା ପରିମାଣ ଅନଲାଇନରେ ପଞ୍ଜୀକରଣ କରନ୍ତୁ।', 'slot': '2. ସ୍ଲଟ୍ ବୁକିଂ', 'slot_desc': 'ବଡ଼ ଭିଡ଼ରେ ଅପେକ୍ଷା ନକରି ଉପଲବ୍ଧ କ୍ରୟ ସ୍ଲଟ୍ ବାଛନ୍ତୁ।', 'token': '3. ଡିଜିଟାଲ୍ ଟୋକେନ୍', 'token_desc': 'ଟୋକେନ୍ ପାଆନ୍ତୁ ଏବଂ ଧାଡ଼ିରେ ଆପଣଙ୍କ ସ୍ଥାନ ଦେଖନ୍ତୁ।', 'notify': '4. ସ୍ମାର୍ଟ ସୂଚନା', 'notify_desc': 'ଆପଣଙ୍କ ପାଳି ନିକଟତର ହେଲେ ସୂଚନା ପାଆନ୍ତୁ।', 'proc': '5. କ୍ରୟ ଟ୍ରାକିଂ', 'proc_desc': 'ଗୁଣବତ୍ତା ଯାଞ୍ଚ, ଓଜନ ଏବଂ କ୍ରୟ ପ୍ରଗତି ଦେଖନ୍ତୁ।', 'pay': '6. ପେମେଣ୍ଟ ଟ୍ରାକିଂ', 'pay_desc': 'ଆଶା କରାଯାଉଥିବା ରାଶି ଏବଂ ପେମେଣ୍ଟ ସ୍ଥିତି ଦେଖନ୍ତୁ।', 'reg_title': 'ଚାଷୀ ପଞ୍ଜୀକରଣ ଏବଂ ସ୍ଲଟ୍ ବୁକିଂ', 'reg_sub': 'ଡିଜିଟାଲ୍ ଟୋକେନ୍ ପାଇବା ପାଇଁ ଆପଣଙ୍କ ବିବରଣୀ ଦିଅନ୍ତୁ।', 'farmer_name': 'ଚାଷୀଙ୍କ ନାମ', 'mobile': 'ମୋବାଇଲ୍ ନମ୍ବର', 'farmer_id': 'ଚାଷୀ ID', 'crop': 'ଫସଲ', 'quantity': 'ପରିମାଣ (କୁଇଣ୍ଟାଲ୍)', 'available_slot': 'ଉପଲବ୍ଧ ସ୍ଲଟ୍', 'submit': 'ପଞ୍ଜୀକରଣ କରନ୍ତୁ ଏବଂ ଟୋକେନ୍ ପାଆନ୍ତୁ', 'today_slots': 'ଆଜିର ସ୍ଲଟ୍', 'slots_help': 'ସ୍ଲଟ୍ ଚାଷୀଙ୍କ ଆଗମନକୁ ବାଣ୍ଟି ଭିଡ଼ କମାଇବାରେ ସାହାଯ୍ୟ କରେ।', 'live': '🔴 ଲାଇଭ୍ ଧାଡ଼ି ପରିଚାଳନା', 'live_sub': 'ଅନାବଶ୍ୟକ ଅପେକ୍ଷା ନକରି ଆପଣଙ୍କ ଧାଡ଼ି ସ୍ଥିତି ଦେଖନ୍ତୁ।', 'serving': 'ବର୍ତ୍ତମାନ', 'next': 'ପରବର୍ତ୍ତୀ:', 'sample': 'ଆପଣଙ୍କ ନମୁନା ଟୋକେନ୍', 'away': '6 ସ୍ଥାନ ଦୂରରେ', 'simulate': 'ପରବର୍ତ୍ତୀ ଚାଷୀଙ୍କୁ ସିମୁଲେଟ୍ କରନ୍ତୁ', 'status_title': '📦 କ୍ରୟ ଏବଂ ପେମେଣ୍ଟ ସ୍ଥିତି', 'status_sub': 'ବୁକିଂରୁ ପେମେଣ୍ଟ ପର୍ଯ୍ୟନ୍ତ ସମ୍ପୂର୍ଣ୍ଣ ସ୍ୱଚ୍ଛତା।', 'booking': 'ବୁକିଂ', 'arrived': 'ପହଞ୍ଚିଛି', 'queue': 'ଧାଡ଼ି', 'quality': 'ଗୁଣବତ୍ତା ଯାଞ୍ଚ', 'weighing': 'ଓଜନ', 'procurement': 'କ୍ରୟ', 'payment_processing': 'ପେମେଣ୍ଟ ପ୍ରକ୍ରିୟାଧୀନ', 'payment_received': 'ପେମେଣ୍ଟ ପ୍ରାପ୍ତ', 'completed': 'ସମ୍ପୂର୍ଣ୍ଣ ✓', 'processing': 'ପ୍ରକ୍ରିୟାଧୀନ', 'recent': 'ସାମ୍ପ୍ରତିକ ପଞ୍ଜୀକରଣ', 'recent_sub': 'ଡେମୋ ତଥ୍ୟ SQLiteରେ ସଂରକ୍ଷିତ।', 'status': 'ସ୍ଥିତି', 'no_reg': 'ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ପଞ୍ଜୀକରଣ ନାହିଁ।', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 ଡେମୋ | କୃଷି କ୍ରୟ ସ୍ୱୟଂଚାଳନ', 'success': 'ପଞ୍ଜୀକରଣ ସଫଳ! ଆପଣଙ୍କ ଡିଜିଟାଲ୍ ଟୋକେନ୍ {token}। ଆପଣଙ୍କ ପାଳି ନିକଟତର ହେଲେ ସୂଚନା ମିଳିବ।', 'queue_alert': 'ଧାଡ଼ି ଅପଡେଟ୍ ହୋଇଛି! ବର୍ତ୍ତମାନ: {current}\\nଆପଣଙ୍କ P104 ଟୋକେନ୍ ପ୍ରାୟ {ahead} ସ୍ଥାନ ଦୂରରେ।', 'slots_left': '{n}ଟି ସ୍ଲଟ୍ ବାକି', 'full': 'ପୂର୍ଣ୍ଣ'},
'pa': {'name': 'ਪੰਜਾਬੀ', 'home': 'ਹੋਮ', 'register_nav': 'ਰਜਿਸਟ੍ਰੇਸ਼ਨ', 'queue_nav': 'ਲਾਈਵ ਕਤਾਰ', 'status_nav': 'ਸਥਿਤੀ', 'hero_title': 'ਸਮਾਰਟ ਖਰੀਦ,<br>ਜਿੱਥੇ ਨਵੀਨਤਾ ਜੜ੍ਹਾਂ ਫੈਲਾਉਂਦੀ ਹੈ', 'hero_desc': 'ਆਪਣੀ ਫਸਲ ਰਜਿਸਟਰ ਕਰੋ, ਸਮੇਂ ਦਾ ਸਲਾਟ ਬੁੱਕ ਕਰੋ, ਡਿਜ਼ਿਟਲ ਟੋਕਨ ਲਵੋ ਅਤੇ ਖਰੀਦ ਤੇ ਭੁਗਤਾਨ ਦੀ ਸਥਿਤੀ ਇੱਕੋ ਥਾਂ ਵੇਖੋ।', 'book': 'ਸਲਾਟ ਬੁੱਕ ਕਰੋ →', 'centre': '📍 ਖਰੀਦ ਕੇਂਦਰ — ਅੱਜ', 'current_token': 'ਮੌਜੂਦਾ ਟੋਕਨ', 'waiting': 'ਅੰਦਾਜ਼ਨ ਉਡੀਕ ਕਰ ਰਹੇ ਕਿਸਾਨ: 6', 'centre_status': 'ਕੇਂਦਰ ਦੀ ਸਥਿਤੀ:', 'open': '● ਖੁੱਲ੍ਹਾ', 'how_title': 'KisanGati ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ', 'how_desc': 'ਪਾਰਦਰਸ਼ੀ ਖੇਤੀਬਾੜੀ ਖਰੀਦ ਲਈ ਡਿਜ਼ਿਟਲ ਪ੍ਰਕਿਰਿਆ।', 'reg': '1. ਕਿਸਾਨ ਰਜਿਸਟ੍ਰੇਸ਼ਨ', 'reg_desc': 'ਕਿਸਾਨ ਦੀ ਜਾਣਕਾਰੀ, ਫਸਲ ਅਤੇ ਅਨੁਮਾਨਿਤ ਮਾਤਰਾ ਆਨਲਾਈਨ ਰਜਿਸਟਰ ਕਰੋ।', 'slot': '2. ਸਲਾਟ ਬੁਕਿੰਗ', 'slot_desc': 'ਵੱਡੀ ਭੀੜ ਵਿੱਚ ਉਡੀਕ ਕਰਨ ਦੀ ਬਜਾਏ ਉਪਲਬਧ ਖਰੀਦ ਸਲਾਟ ਚੁਣੋ।', 'token': '3. ਡਿਜ਼ਿਟਲ ਟੋਕਨ', 'token_desc': 'ਟੋਕਨ ਲਵੋ ਅਤੇ ਕਤਾਰ ਵਿੱਚ ਆਪਣੀ ਸਥਿਤੀ ਵੇਖੋ.', 'notify': '4. ਸਮਾਰਟ ਸੂਚਨਾਵਾਂ', 'notify_desc': "ਤੁਹਾਡੀ ਵਾਰੀ ਨੇੜੇ ਆਉਣ 'ਤੇ ਸੂਚਨਾ ਲਵੋ.", 'proc': '5. ਖਰੀਦ ਟ੍ਰੈਕਿੰਗ', 'proc_desc': 'ਗੁਣਵੱਤਾ ਜਾਂਚ, ਤੋਲ ਅਤੇ ਖਰੀਦ ਦੀ ਤਰੱਕੀ ਵੇਖੋ.', 'pay': '6. ਭੁਗਤਾਨ ਟ੍ਰੈਕਿੰਗ', 'pay_desc': 'ਉਮੀਦ ਕੀਤੀ ਰਕਮ ਅਤੇ ਭੁਗਤਾਨ ਦੀ ਸਥਿਤੀ ਵੇਖੋ.', 'reg_title': 'ਕਿਸਾਨ ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਅਤੇ ਸਲਾਟ ਬੁਕਿੰਗ', 'reg_sub': 'ਡਿਜ਼ਿਟਲ ਟੋਕਨ ਲੈਣ ਲਈ ਆਪਣੀ ਜਾਣਕਾਰੀ ਦਿਓ.', 'farmer_name': 'ਕਿਸਾਨ ਦਾ ਨਾਮ', 'mobile': 'ਮੋਬਾਈਲ ਨੰਬਰ', 'farmer_id': 'ਕਿਸਾਨ ID', 'crop': 'ਫਸਲ', 'quantity': 'ਮਾਤਰਾ (ਕੁਇੰਟਲ)', 'available_slot': 'ਉਪਲਬਧ ਸਲਾਟ', 'submit': 'ਰਜਿਸਟਰ ਕਰੋ ਅਤੇ ਟੋਕਨ ਲਵੋ', 'today_slots': 'ਅੱਜ ਦੇ ਸਲਾਟ', 'slots_help': 'ਸਲਾਟ ਕਿਸਾਨਾਂ ਦੇ ਆਉਣ ਨੂੰ ਵੰਡ ਕੇ ਭੀੜ ਘਟਾਉਣ ਵਿੱਚ ਮਦਦ ਕਰਦੇ ਹਨ.', 'live': '🔴 ਲਾਈਵ ਕਤਾਰ ਪ੍ਰਬੰਧਨ', 'live_sub': 'ਬਿਨਾਂ ਲੋੜ ਉਡੀਕ ਕੀਤੇ ਆਪਣੀ ਕਤਾਰ ਦੀ ਸਥਿਤੀ ਵੇਖੋ.', 'serving': 'ਹੁਣ ਚੱਲ ਰਿਹਾ ਹੈ', 'next': 'ਅਗਲਾ:', 'sample': 'ਤੁਹਾਡਾ ਨਮੂਨਾ ਟੋਕਨ', 'away': '6 ਸਥਾਨ ਦੂਰ', 'simulate': 'ਅਗਲੇ ਕਿਸਾਨ ਦੀ ਸਿਮੂਲੇਸ਼ਨ', 'status_title': '📦 ਖਰੀਦ ਅਤੇ ਭੁਗਤਾਨ ਦੀ ਸਥਿਤੀ', 'status_sub': 'ਬੁਕਿੰਗ ਤੋਂ ਭੁਗਤਾਨ ਤੱਕ ਪੂਰੀ ਪਾਰਦਰਸ਼ਤਾ.', 'booking': 'ਬੁਕਿੰਗ', 'arrived': 'ਪਹੁੰਚਿਆ', 'queue': 'ਕਤਾਰ', 'quality': 'ਗੁਣਵੱਤਾ ਜਾਂਚ', 'weighing': 'ਤੋਲ', 'procurement': 'ਖਰੀਦ', 'payment_processing': 'ਭੁਗਤਾਨ ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ', 'payment_received': 'ਭੁਗਤਾਨ ਪ੍ਰਾਪਤ', 'completed': 'ਪੂਰਾ ✓', 'processing': 'ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ', 'recent': 'ਹਾਲੀਆ ਰਜਿਸਟ੍ਰੇਸ਼ਨਾਂ', 'recent_sub': 'ਡੈਮੋ ਡਾਟਾ SQLite ਵਿੱਚ ਸਟੋਰ ਹੈ.', 'status': 'ਸਥਿਤੀ', 'no_reg': 'ਅਜੇ ਕੋਈ ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਨਹੀਂ.', 'footer': '🌾 KisanGati — Smart India Hackathon SIH26032 ਡੈਮੋ | ਖੇਤੀਬਾੜੀ ਖਰੀਦ ਆਟੋਮੇਸ਼ਨ', 'success': "ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਸਫਲ! ਤੁਹਾਡਾ ਡਿਜ਼ਿਟਲ ਟੋਕਨ {token} ਹੈ। ਤੁਹਾਡੀ ਵਾਰੀ ਨੇੜੇ ਆਉਣ 'ਤੇ ਸੂਚਨਾ ਮਿਲੇਗੀ.", 'queue_alert': 'ਕਤਾਰ ਅਪਡੇਟ ਹੋ ਗਈ! ਹੁਣ ਚੱਲ ਰਿਹਾ ਹੈ: {current}\\nਤੁਹਾਡਾ P104 ਟੋਕਨ ਲਗਭਗ {ahead} ਸਥਾਨ ਦੂਰ ਹੈ.', 'slots_left': '{n} ਸਲਾਟ ਬਾਕੀ', 'full': 'ਭਰਿਆ ਹੋਇਆ'}
}
# Weather-assistance labels. English is used as a safe fallback for languages
# that do not yet have dedicated weather translations.
_WEATHER_EN = {
    "weather_title": "🌦️ Weather Assistance",
    "weather_sub": "Current weather for your location with farming safety warnings.",
    "weather_getting": "Getting your current location and weather...",
    "weather_enable": "Allow location access to see local weather.",
    "weather_location": "Location",
    "weather_humidity": "Humidity",
    "weather_wind": "Wind",
    "weather_rain": "Rain chance",
    "weather_safe": "Weather looks suitable for normal farm activities.",
    "weather_rain_warn": "Rain is likely. Consider delaying spraying, harvesting or transport.",
    "weather_storm_warn": "Severe weather risk. Avoid open fields and postpone outdoor farm work.",
    "weather_heat_warn": "High temperature. Take breaks, drink water and avoid heavy work in peak heat.",
    "weather_wind_warn": "Strong winds expected. Secure crops, equipment and temporary structures.",
    "weather_error": "Weather could not be loaded. Please allow location access and try again.",
    "weather_refresh": "Refresh Weather"
}
for _code, _vals in {
    "en": {
        "weather_title":"🌦️ Weather Assistance","weather_sub":"Current weather for your location with farming safety warnings.",
        "weather_getting":"Getting your current location and weather...","weather_enable":"Allow location access to see local weather.",
        "weather_location":"Location","weather_humidity":"Humidity","weather_wind":"Wind","weather_rain":"Rain chance",
        "weather_safe":"Weather looks suitable for normal farm activities.","weather_rain_warn":"Rain is likely. Consider delaying spraying, harvesting or transport.",
        "weather_storm_warn":"Severe weather risk. Avoid open fields and postpone outdoor farm work.","weather_heat_warn":"High temperature. Take breaks, drink water and avoid heavy work in peak heat.",
        "weather_wind_warn":"Strong winds expected. Secure crops, equipment and temporary structures.","weather_error":"Weather could not be loaded. Please allow location access and try again.",
        "weather_refresh":"Refresh Weather"
    },
    "hi": {
        "weather_title":"🌦️ मौसम सहायता","weather_sub":"आपके स्थान का वर्तमान मौसम और खेती के लिए सुरक्षा चेतावनी।",
        "weather_getting":"आपका स्थान और मौसम प्राप्त किया जा रहा है...","weather_enable":"स्थानीय मौसम देखने के लिए स्थान की अनुमति दें।",
        "weather_location":"स्थान","weather_humidity":"नमी","weather_wind":"हवा","weather_rain":"बारिश की संभावना",
        "weather_safe":"मौसम सामान्य कृषि कार्यों के लिए अनुकूल है।","weather_rain_warn":"बारिश की संभावना है। छिड़काव, कटाई या परिवहन थोड़ी देर के लिए टालें।",
        "weather_storm_warn":"खराब मौसम का खतरा है। खुले खेत में न जाएं और बाहरी काम टालें।","weather_heat_warn":"तापमान अधिक है। पानी पिएं, आराम करें और तेज गर्मी में भारी काम न करें।",
        "weather_wind_warn":"तेज हवाएं चल सकती हैं। फसल, उपकरण और अस्थायी ढांचे सुरक्षित करें।","weather_error":"मौसम लोड नहीं हो सका। स्थान की अनुमति दें और फिर प्रयास करें।",
        "weather_refresh":"मौसम रीफ्रेश करें"
    },
    "bn": {
        "weather_title":"🌦️ আবহাওয়া সহায়তা","weather_sub":"আপনার এলাকার বর্তমান আবহাওয়া ও কৃষি নিরাপত্তা সতর্কতা।",
        "weather_getting":"আপনার অবস্থান ও আবহাওয়া নেওয়া হচ্ছে...","weather_enable":"স্থানীয় আবহাওয়া দেখতে অবস্থানের অনুমতি দিন।",
        "weather_location":"অবস্থান","weather_humidity":"আর্দ্রতা","weather_wind":"বাতাস","weather_rain":"বৃষ্টির সম্ভাবনা",
        "weather_safe":"স্বাভাবিক কৃষিকাজের জন্য আবহাওয়া উপযুক্ত।","weather_rain_warn":"বৃষ্টির সম্ভাবনা আছে। স্প্রে, ফসল কাটা বা পরিবহন কিছুটা পিছিয়ে দিন।",
        "weather_storm_warn":"খারাপ আবহাওয়ার ঝুঁকি আছে। খোলা মাঠ এড়িয়ে চলুন।","weather_heat_warn":"তাপমাত্রা বেশি। পানি পান করুন, বিরতি নিন এবং অতিরিক্ত গরমে ভারী কাজ এড়ান।",
        "weather_wind_warn":"জোরে বাতাস হতে পারে। ফসল, সরঞ্জাম ও অস্থায়ী কাঠামো নিরাপদ করুন।","weather_error":"আবহাওয়া লোড করা যায়নি। অবস্থানের অনুমতি দিয়ে আবার চেষ্টা করুন।",
        "weather_refresh":"আবহাওয়া রিফ্রেশ করুন"
    }
}.items():
    TRANSLATIONS[_code].update(_vals)
for _code in TRANSLATIONS:
    for _key, _value in _WEATHER_EN.items():
        TRANSLATIONS[_code].setdefault(_key, _value)

# ---------------- BANK + GPS / TRACKING TRANSLATIONS ----------------
_NEW_FEATURE_TRANSLATIONS = {'en': {'bank_title': '🏦 Bank Details',
        'bank_help': "Add the farmer's bank details for transparent payment processing.",
        'bank_name': 'Bank Name',
        'bank_name_ph': 'e.g. State Bank of India',
        'account_holder': 'Account Holder Name',
        'account_holder_ph': 'As per bank account',
        'account_number': 'Account Number',
        'account_number_ph': '9–18 digit account number',
        'ifsc': 'IFSC Code',
        'ifsc_ph': 'e.g. SBIN0001234',
        'tracking_title': '📍 Live Shipment & Processing Tracking',
        'tracking_sub': 'Track where your procurement lot is currently being processed or shipped.',
        'tracking_token_ph': 'Enter token e.g. P101',
        'track_lot': 'Track My Lot',
        'tracking_empty': 'Register a farmer first, then enter the digital token to view its tracking details.',
        'tracking_id': 'Tracking ID',
        'current_stage': 'Current Stage',
        'current_location': 'Current Location',
        'last_gps': 'Last GPS Update',
        'start_gps': '📡 Start GPS Tracking',
        'stop_gps': '⏹ Stop GPS Tracking',
        'simulate_stage': '🔄 Simulate Next Stage',
        'stage_centre': 'At Procurement Centre',
        'stage_quality': 'Quality Check',
        'stage_weighing': 'Weighing',
        'stage_processing': 'Processing',
        'stage_shipped': 'Shipped',
        'stage_transit': 'In Transit',
        'stage_delivered': 'Delivered',
        'loc_centre': 'Procurement Centre',
        'loc_quality': 'Quality Check Unit',
        'loc_weighing': 'Weighing Bay',
        'loc_processing': 'Processing Unit',
        'loc_dispatch': 'Dispatch Centre',
        'loc_live': 'Live GPS Location',
        'loc_destination': 'Destination Centre',
        'gps_active': '🟢 GPS tracking is active and sending location updates.',
        'gps_stopped': 'GPS tracking is currently stopped.',
        'gps_permission': '📡 Requesting GPS permission...',
        'gps_live': '🟢 GPS live • Accuracy ±{accuracy} m • Last update {time}',
        'gps_error': 'GPS error: {message}',
        'gps_update_error': 'GPS update error: {message}',
        'tracking_not_found': 'Tracking record not found',
        'valid_token': 'Enter a valid token such as P101.',
        'load_token_first': 'Load a tracking token first.',
        'gps_unsupported': 'GPS/geolocation is not supported by this browser.',
        'lot_delivered': 'The lot is already marked Delivered.',
        'tracking_load_error': 'Unable to load tracking details.',
        'tracking_update_error': 'Unable to update tracking stage.',
        'tracking_id_success': ' Tracking ID: {tracking_id}.',
        'valid_mobile': 'Please enter a valid 10-digit mobile number.',
        'valid_account': 'Please enter a valid 9–18 digit bank account number.',
        'valid_ifsc': 'Please enter a valid 11-character IFSC code.'},
 'hi': {'bank_title': '🏦 बैंक विवरण',
        'bank_help': 'पारदर्शी भुगतान प्रक्रिया के लिए किसान के बैंक विवरण जोड़ें।',
        'bank_name': 'बैंक का नाम',
        'bank_name_ph': 'जैसे: भारतीय स्टेट बैंक',
        'account_holder': 'खाता धारक का नाम',
        'account_holder_ph': 'बैंक खाते के अनुसार',
        'account_number': 'खाता संख्या',
        'account_number_ph': '9–18 अंकों की खाता संख्या',
        'ifsc': 'IFSC कोड',
        'ifsc_ph': 'जैसे: SBIN0001234',
        'tracking_title': '📍 लाइव शिपमेंट और प्रोसेसिंग ट्रैकिंग',
        'tracking_sub': 'देखें कि आपकी खरीद की खेप अभी कहाँ संसाधित या भेजी जा रही है।',
        'tracking_token_ph': 'टोकन दर्ज करें जैसे P101',
        'track_lot': 'मेरी खेप ट्रैक करें',
        'tracking_empty': 'पहले किसान का पंजीकरण करें, फिर डिजिटल टोकन दर्ज करके ट्रैकिंग विवरण देखें।',
        'tracking_id': 'ट्रैकिंग ID',
        'current_stage': 'वर्तमान चरण',
        'current_location': 'वर्तमान स्थान',
        'last_gps': 'अंतिम GPS अपडेट',
        'start_gps': '📡 GPS ट्रैकिंग शुरू करें',
        'stop_gps': '⏹ GPS ट्रैकिंग रोकें',
        'simulate_stage': '🔄 अगला चरण सिमुलेट करें',
        'stage_centre': 'खरीद केंद्र पर',
        'stage_quality': 'गुणवत्ता जांच',
        'stage_weighing': 'वजन',
        'stage_processing': 'प्रसंस्करण',
        'stage_shipped': 'भेजा गया',
        'stage_transit': 'रास्ते में',
        'stage_delivered': 'डिलीवर हो गया',
        'loc_centre': 'खरीद केंद्र',
        'loc_quality': 'गुणवत्ता जांच इकाई',
        'loc_weighing': 'वजन केंद्र',
        'loc_processing': 'प्रसंस्करण इकाई',
        'loc_dispatch': 'डिस्पैच केंद्र',
        'loc_live': 'लाइव GPS स्थान',
        'loc_destination': 'गंतव्य केंद्र',
        'gps_active': '🟢 GPS ट्रैकिंग सक्रिय है और स्थान अपडेट भेज रही है।',
        'gps_stopped': 'GPS ट्रैकिंग अभी बंद है।',
        'gps_permission': '📡 GPS अनुमति मांगी जा रही है...',
        'gps_live': '🟢 GPS लाइव • सटीकता ±{accuracy} मीटर • अंतिम अपडेट {time}',
        'gps_error': 'GPS त्रुटि: {message}',
        'gps_update_error': 'GPS अपडेट त्रुटि: {message}',
        'tracking_not_found': 'ट्रैकिंग रिकॉर्ड नहीं मिला',
        'valid_token': 'P101 जैसे मान्य टोकन दर्ज करें।',
        'load_token_first': 'पहले ट्रैकिंग टोकन लोड करें।',
        'gps_unsupported': 'इस ब्राउज़र में GPS/जियोलोकेशन समर्थित नहीं है।',
        'lot_delivered': 'खेप पहले ही डिलीवर के रूप में चिह्नित है।',
        'tracking_load_error': 'ट्रैकिंग विवरण लोड नहीं हो सका।',
        'tracking_update_error': 'ट्रैकिंग चरण अपडेट नहीं हो सका।',
        'tracking_id_success': ' ट्रैकिंग ID: {tracking_id}.',
        'valid_mobile': 'कृपया मान्य 10 अंकों का मोबाइल नंबर दर्ज करें।',
        'valid_account': 'कृपया मान्य 9–18 अंकों की बैंक खाता संख्या दर्ज करें।',
        'valid_ifsc': 'कृपया मान्य 11-अक्षर का IFSC कोड दर्ज करें।'},
 'bn': {'bank_title': '🏦 ব্যাংক তথ্য',
        'bank_help': 'স্বচ্ছ পেমেন্ট প্রক্রিয়ার জন্য কৃষকের ব্যাংক তথ্য যোগ করুন।',
        'bank_name': 'ব্যাংকের নাম',
        'bank_name_ph': 'যেমন: স্টেট ব্যাংক অফ ইন্ডিয়া',
        'account_holder': 'অ্যাকাউন্টধারীর নাম',
        'account_holder_ph': 'ব্যাংক অ্যাকাউন্ট অনুযায়ী',
        'account_number': 'অ্যাকাউন্ট নম্বর',
        'account_number_ph': '৯–১৮ সংখ্যার অ্যাকাউন্ট নম্বর',
        'ifsc': 'IFSC কোড',
        'ifsc_ph': 'যেমন: SBIN0001234',
        'tracking_title': '📍 লাইভ শিপমেন্ট ও প্রসেসিং ট্র্যাকিং',
        'tracking_sub': 'আপনার ক্রয় করা পণ্যটি বর্তমানে কোথায় প্রক্রিয়াকরণ বা পাঠানো হচ্ছে তা দেখুন।',
        'tracking_token_ph': 'টোকেন লিখুন, যেমন P101',
        'track_lot': 'আমার পণ্য ট্র্যাক করুন',
        'tracking_empty': 'প্রথমে কৃষক নিবন্ধন করুন, তারপর ডিজিটাল টোকেন দিয়ে ট্র্যাকিং তথ্য দেখুন।',
        'tracking_id': 'ট্র্যাকিং ID',
        'current_stage': 'বর্তমান ধাপ',
        'current_location': 'বর্তমান অবস্থান',
        'last_gps': 'শেষ GPS আপডেট',
        'start_gps': '📡 GPS ট্র্যাকিং শুরু করুন',
        'stop_gps': '⏹ GPS ট্র্যাকিং বন্ধ করুন',
        'simulate_stage': '🔄 পরবর্তী ধাপ সিমুলেট করুন',
        'stage_centre': 'ক্রয় কেন্দ্রে',
        'stage_quality': 'মান পরীক্ষা',
        'stage_weighing': 'ওজন',
        'stage_processing': 'প্রক্রিয়াকরণ',
        'stage_shipped': 'পাঠানো হয়েছে',
        'stage_transit': 'পথে আছে',
        'stage_delivered': 'ডেলিভারি সম্পন্ন',
        'loc_centre': 'ক্রয় কেন্দ্র',
        'loc_quality': 'মান পরীক্ষা ইউনিট',
        'loc_weighing': 'ওজন কেন্দ্র',
        'loc_processing': 'প্রক্রিয়াকরণ ইউনিট',
        'loc_dispatch': 'ডিসপ্যাচ কেন্দ্র',
        'loc_live': 'লাইভ GPS অবস্থান',
        'loc_destination': 'গন্তব্য কেন্দ্র',
        'gps_active': '🟢 GPS ট্র্যাকিং সক্রিয় এবং অবস্থানের আপডেট পাঠানো হচ্ছে।',
        'gps_stopped': 'GPS ট্র্যাকিং বর্তমানে বন্ধ।',
        'gps_permission': '📡 GPS অনুমতির অনুরোধ করা হচ্ছে...',
        'gps_live': '🟢 GPS লাইভ • নির্ভুলতা ±{accuracy} মিটার • শেষ আপডেট {time}',
        'gps_error': 'GPS ত্রুটি: {message}',
        'gps_update_error': 'GPS আপডেট ত্রুটি: {message}',
        'tracking_not_found': 'ট্র্যাকিং রেকর্ড পাওয়া যায়নি',
        'valid_token': 'P101-এর মতো একটি বৈধ টোকেন লিখুন।',
        'load_token_first': 'প্রথমে একটি ট্র্যাকিং টোকেন লোড করুন।',
        'gps_unsupported': 'এই ব্রাউজারে GPS/জিওলোকেশন সমর্থিত নয়।',
        'lot_delivered': 'পণ্যটি ইতিমধ্যে ডেলিভারি সম্পন্ন হিসেবে চিহ্নিত।',
        'tracking_load_error': 'ট্র্যাকিং তথ্য লোড করা যায়নি।',
        'tracking_update_error': 'ট্র্যাকিং ধাপ আপডেট করা যায়নি।',
        'tracking_id_success': ' ট্র্যাকিং ID: {tracking_id}.',
        'valid_mobile': 'দয়া করে একটি বৈধ ১০ সংখ্যার মোবাইল নম্বর দিন।',
        'valid_account': 'দয়া করে একটি বৈধ ৯–১৮ সংখ্যার ব্যাংক অ্যাকাউন্ট নম্বর দিন।',
        'valid_ifsc': 'দয়া করে একটি বৈধ ১১ অক্ষরের IFSC কোড দিন।'},
 'ta': {'bank_title': '🏦 வங்கி விவரங்கள்',
        'bank_help': 'வெளிப்படையான பணப்பரிவர்த்தனைக்காக விவசாயியின் வங்கி விவரங்களைச் சேர்க்கவும்.',
        'bank_name': 'வங்கியின் பெயர்',
        'bank_name_ph': 'எ.கா.: ஸ்டேட் பேங்க் ஆஃப் இந்தியா',
        'account_holder': 'கணக்கு வைத்திருப்பவரின் பெயர்',
        'account_holder_ph': 'வங்கி கணக்கில் உள்ளபடி',
        'account_number': 'கணக்கு எண்',
        'account_number_ph': '9–18 இலக்க கணக்கு எண்',
        'ifsc': 'IFSC குறியீடு',
        'ifsc_ph': 'எ.கா.: SBIN0001234',
        'tracking_title': '📍 நேரடி சரக்கு அனுப்பல் & செயலாக்க கண்காணிப்பு',
        'tracking_sub': 'உங்கள் கொள்முதல் சரக்கு தற்போது எங்கு செயலாக்கப்படுகிறது அல்லது அனுப்பப்படுகிறது என்பதைப் பார்க்கவும்.',
        'tracking_token_ph': 'டோக்கனை உள்ளிடவும், எ.கா. P101',
        'track_lot': 'என் சரக்கை கண்காணிக்கவும்',
        'tracking_empty': 'முதலில் விவசாயியைப் பதிவு செய்து, பின்னர் டிஜிட்டல் டோக்கனை உள்ளிட்டு கண்காணிப்பு விவரங்களைப் பார்க்கவும்.',
        'tracking_id': 'கண்காணிப்பு ID',
        'current_stage': 'தற்போதைய நிலை',
        'current_location': 'தற்போதைய இடம்',
        'last_gps': 'கடைசி GPS புதுப்பிப்பு',
        'start_gps': '📡 GPS கண்காணிப்பை தொடங்கு',
        'stop_gps': '⏹ GPS கண்காணிப்பை நிறுத்து',
        'simulate_stage': '🔄 அடுத்த நிலையை உருவகப்படுத்து',
        'stage_centre': 'கொள்முதல் மையத்தில்',
        'stage_quality': 'தரச் சோதனை',
        'stage_weighing': 'எடை',
        'stage_processing': 'செயலாக்கம்',
        'stage_shipped': 'அனுப்பப்பட்டது',
        'stage_transit': 'பயணத்தில்',
        'stage_delivered': 'வழங்கப்பட்டது',
        'loc_centre': 'கொள்முதல் மையம்',
        'loc_quality': 'தரச் சோதனை பிரிவு',
        'loc_weighing': 'எடை மையம்',
        'loc_processing': 'செயலாக்க பிரிவு',
        'loc_dispatch': 'அனுப்பும் மையம்',
        'loc_live': 'நேரடி GPS இடம்',
        'loc_destination': 'இலக்கு மையம்',
        'gps_active': '🟢 GPS கண்காணிப்பு செயல்பாட்டில் உள்ளது மற்றும் இருப்பிட புதுப்பிப்புகள் அனுப்பப்படுகின்றன.',
        'gps_stopped': 'GPS கண்காணிப்பு தற்போது நிறுத்தப்பட்டுள்ளது.',
        'gps_permission': '📡 GPS அனுமதி கோரப்படுகிறது...',
        'gps_live': '🟢 GPS நேரலை • துல்லியம் ±{accuracy} மீ • கடைசி புதுப்பிப்பு {time}',
        'gps_error': 'GPS பிழை: {message}',
        'gps_update_error': 'GPS புதுப்பிப்பு பிழை: {message}',
        'tracking_not_found': 'கண்காணிப்பு பதிவு கிடைக்கவில்லை',
        'valid_token': 'P101 போன்ற சரியான டோக்கனை உள்ளிடவும்.',
        'load_token_first': 'முதலில் கண்காணிப்பு டோக்கனை ஏற்றவும்.',
        'gps_unsupported': 'இந்த உலாவியில் GPS/புவியிடமறிதல் ஆதரிக்கப்படவில்லை.',
        'lot_delivered': 'சரக்கு ஏற்கனவே வழங்கப்பட்டதாக குறிக்கப்பட்டுள்ளது.',
        'tracking_load_error': 'கண்காணிப்பு விவரங்களை ஏற்ற முடியவில்லை.',
        'tracking_update_error': 'கண்காணிப்பு நிலையை புதுப்பிக்க முடியவில்லை.',
        'tracking_id_success': ' கண்காணிப்பு ID: {tracking_id}.',
        'valid_mobile': 'சரியான 10 இலக்க மொபைல் எண்ணை உள்ளிடவும்.',
        'valid_account': 'சரியான 9–18 இலக்க வங்கி கணக்கு எண்ணை உள்ளிடவும்.',
        'valid_ifsc': 'சரியான 11 எழுத்து IFSC குறியீட்டை உள்ளிடவும்.'},
 'as': {'bank_title': '🏦 বেংকৰ বিৱৰণ',
        'bank_help': 'স্বচ্ছ পেমেণ্ট প্ৰক্ৰিয়াৰ বাবে কৃষকৰ বেংকৰ বিৱৰণ যোগ কৰক।',
        'bank_name': 'বেংকৰ নাম',
        'bank_name_ph': 'উদাহৰণ: ষ্টেট বেংক অৱ ইণ্ডিয়া',
        'account_holder': 'একাউণ্টধাৰীৰ নাম',
        'account_holder_ph': 'বেংক একাউণ্ট অনুসৰি',
        'account_number': 'একাউণ্ট নম্বৰ',
        'account_number_ph': '৯–১৮ অংকৰ একাউণ্ট নম্বৰ',
        'ifsc': "IFSC ক'ড",
        'ifsc_ph': 'উদাহৰণ: SBIN0001234',
        'tracking_title': '📍 লাইভ শিপমেণ্ট আৰু প্ৰক্ৰিয়াকৰণ ট্ৰেকিং',
        'tracking_sub': "আপোনাৰ ক্ৰয়ৰ সামগ্ৰী বৰ্তমান ক'ত প্ৰক্ৰিয়াকৰণ বা প্ৰেৰণ কৰা হৈছে চাওক।",
        'tracking_token_ph': 'টোকেন দিয়ক, যেনে P101',
        'track_lot': 'মোৰ সামগ্ৰী ট্ৰেক কৰক',
        'tracking_empty': 'প্ৰথমে কৃষক পঞ্জীয়ন কৰক, তাৰ পিছত ডিজিটেল টোকেন দি ট্ৰেকিং বিৱৰণ চাওক।',
        'tracking_id': 'ট্ৰেকিং ID',
        'current_stage': 'বৰ্তমান পৰ্যায়',
        'current_location': 'বৰ্তমান স্থান',
        'last_gps': 'শেষ GPS আপডেট',
        'start_gps': '📡 GPS ট্ৰেকিং আৰম্ভ কৰক',
        'stop_gps': '⏹ GPS ট্ৰেকিং বন্ধ কৰক',
        'simulate_stage': '🔄 পৰৱৰ্তী পৰ্যায় অনুকৰণ কৰক',
        'stage_centre': 'ক্ৰয় কেন্দ্ৰত',
        'stage_quality': 'গুণগত পৰীক্ষা',
        'stage_weighing': 'ওজন',
        'stage_processing': 'প্ৰক্ৰিয়াকৰণ',
        'stage_shipped': 'প্ৰেৰণ কৰা হৈছে',
        'stage_transit': 'পথত আছে',
        'stage_delivered': 'ডেলিভাৰী সম্পন্ন',
        'loc_centre': 'ক্ৰয় কেন্দ্ৰ',
        'loc_quality': 'গুণগত পৰীক্ষা ইউনিট',
        'loc_weighing': 'ওজন কেন্দ্ৰ',
        'loc_processing': 'প্ৰক্ৰিয়াকৰণ ইউনিট',
        'loc_dispatch': 'ডিস্পেচ কেন্দ্ৰ',
        'loc_live': 'লাইভ GPS স্থান',
        'loc_destination': 'গন্তব্য কেন্দ্ৰ',
        'gps_active': '🟢 GPS ট্ৰেকিং সক্ৰিয় আৰু স্থানৰ আপডেট পঠোৱা হৈছে।',
        'gps_stopped': 'GPS ট্ৰেকিং বৰ্তমান বন্ধ আছে।',
        'gps_permission': '📡 GPS অনুমতি বিচৰা হৈছে...',
        'gps_live': '🟢 GPS লাইভ • সঠিকতা ±{accuracy} মিটাৰ • শেষ আপডেট {time}',
        'gps_error': 'GPS ত্ৰুটি: {message}',
        'gps_update_error': 'GPS আপডেট ত্ৰুটি: {message}',
        'tracking_not_found': "ট্ৰেকিং ৰেকৰ্ড পোৱা নগ'ল",
        'valid_token': 'P101ৰ দৰে এটা বৈধ টোকেন দিয়ক।',
        'load_token_first': 'প্ৰথমে এটা ট্ৰেকিং টোকেন লোড কৰক।',
        'gps_unsupported': "এই ব্ৰাউজাৰত GPS/জিঅ'লকেচন সমৰ্থিত নহয়।",
        'lot_delivered': 'সামগ্ৰী ইতিমধ্যে ডেলিভাৰী সম্পন্ন বুলি চিহ্নিত কৰা হৈছে।',
        'tracking_load_error': "ট্ৰেকিং বিৱৰণ লোড কৰিব পৰা নগ'ল।",
        'tracking_update_error': "ট্ৰেকিং পৰ্যায় আপডেট কৰিব পৰা নগ'ল।",
        'tracking_id_success': ' ট্ৰেকিং ID: {tracking_id}.',
        'valid_mobile': 'এটা বৈধ ১০ অংকৰ মোবাইল নম্বৰ দিয়ক।',
        'valid_account': 'এটা বৈধ ৯–১৮ অংকৰ বেংক একাউণ্ট নম্বৰ দিয়ক।',
        'valid_ifsc': "এটা বৈধ ১১ আখৰৰ IFSC ক'ড দিয়ক।"},
 'te': {'bank_title': '🏦 బ్యాంక్ వివరాలు',
        'bank_help': 'పారదర్శక చెల్లింపు ప్రక్రియ కోసం రైతు బ్యాంక్ వివరాలను జోడించండి.',
        'bank_name': 'బ్యాంక్ పేరు',
        'bank_name_ph': 'ఉదా: స్టేట్ బ్యాంక్ ఆఫ్ ఇండియా',
        'account_holder': 'ఖాతాదారుని పేరు',
        'account_holder_ph': 'బ్యాంక్ ఖాతాలో ఉన్నట్లుగా',
        'account_number': 'ఖాతా నంబర్',
        'account_number_ph': '9–18 అంకెల ఖాతా నంబర్',
        'ifsc': 'IFSC కోడ్',
        'ifsc_ph': 'ఉదా: SBIN0001234',
        'tracking_title': '📍 లైవ్ షిప్\u200cమెంట్ & ప్రాసెసింగ్ ట్రాకింగ్',
        'tracking_sub': 'మీ కొనుగోలు సరుకు ప్రస్తుతం ఎక్కడ ప్రాసెస్ అవుతోంది లేదా పంపబడుతోంది చూడండి.',
        'tracking_token_ph': 'టోకెన్ నమోదు చేయండి, ఉదా. P101',
        'track_lot': 'నా సరుకును ట్రాక్ చేయండి',
        'tracking_empty': 'ముందుగా రైతును నమోదు చేసి, తర్వాత డిజిటల్ టోకెన్ నమోదు చేసి ట్రాకింగ్ వివరాలు చూడండి.',
        'tracking_id': 'ట్రాకింగ్ ID',
        'current_stage': 'ప్రస్తుత దశ',
        'current_location': 'ప్రస్తుత స్థానం',
        'last_gps': 'చివరి GPS నవీకరణ',
        'start_gps': '📡 GPS ట్రాకింగ్ ప్రారంభించండి',
        'stop_gps': '⏹ GPS ట్రాకింగ్ ఆపండి',
        'simulate_stage': '🔄 తదుపరి దశను అనుకరించండి',
        'stage_centre': 'కొనుగోలు కేంద్రంలో',
        'stage_quality': 'నాణ్యత తనిఖీ',
        'stage_weighing': 'బరువు',
        'stage_processing': 'ప్రాసెసింగ్',
        'stage_shipped': 'పంపబడింది',
        'stage_transit': 'రవాణాలో ఉంది',
        'stage_delivered': 'డెలివరీ పూర్తైంది',
        'loc_centre': 'కొనుగోలు కేంద్రం',
        'loc_quality': 'నాణ్యత తనిఖీ యూనిట్',
        'loc_weighing': 'బరువు కేంద్రం',
        'loc_processing': 'ప్రాసెసింగ్ యూనిట్',
        'loc_dispatch': 'డిస్పాచ్ కేంద్రం',
        'loc_live': 'లైవ్ GPS స్థానం',
        'loc_destination': 'గమ్య కేంద్రం',
        'gps_active': '🟢 GPS ట్రాకింగ్ సక్రియంగా ఉంది మరియు స్థాన నవీకరణలు పంపబడుతున్నాయి.',
        'gps_stopped': 'GPS ట్రాకింగ్ ప్రస్తుతం ఆపివేయబడింది.',
        'gps_permission': '📡 GPS అనుమతి కోరుతోంది...',
        'gps_live': '🟢 GPS లైవ్ • ఖచ్చితత్వం ±{accuracy} మీ • చివరి నవీకరణ {time}',
        'gps_error': 'GPS లోపం: {message}',
        'gps_update_error': 'GPS నవీకరణ లోపం: {message}',
        'tracking_not_found': 'ట్రాకింగ్ రికార్డు కనుగొనబడలేదు',
        'valid_token': 'P101 వంటి చెల్లుబాటు అయ్యే టోకెన్ నమోదు చేయండి.',
        'load_token_first': 'ముందుగా ట్రాకింగ్ టోకెన్ లోడ్ చేయండి.',
        'gps_unsupported': 'ఈ బ్రౌజర్\u200cలో GPS/జియోలొకేషన్\u200cకు మద్దతు లేదు.',
        'lot_delivered': 'సరుకు ఇప్పటికే డెలివరీ అయినట్లు గుర్తించబడింది.',
        'tracking_load_error': 'ట్రాకింగ్ వివరాలను లోడ్ చేయలేకపోయాం.',
        'tracking_update_error': 'ట్రాకింగ్ దశను నవీకరించలేకపోయాం.',
        'tracking_id_success': ' ట్రాకింగ్ ID: {tracking_id}.',
        'valid_mobile': 'చెల్లుబాటు అయ్యే 10 అంకెల మొబైల్ నంబర్ నమోదు చేయండి.',
        'valid_account': 'చెల్లుబాటు అయ్యే 9–18 అంకెల బ్యాంక్ ఖాతా నంబర్ నమోదు చేయండి.',
        'valid_ifsc': 'చెల్లుబాటు అయ్యే 11 అక్షరాల IFSC కోడ్ నమోదు చేయండి.'},
 'mr': {'bank_title': '🏦 बँक तपशील',
        'bank_help': 'पारदर्शक पेमेंट प्रक्रियेसाठी शेतकऱ्याचे बँक तपशील जोडा.',
        'bank_name': 'बँकेचे नाव',
        'bank_name_ph': 'उदा.: स्टेट बँक ऑफ इंडिया',
        'account_holder': 'खातेदाराचे नाव',
        'account_holder_ph': 'बँक खात्याप्रमाणे',
        'account_number': 'खाते क्रमांक',
        'account_number_ph': '9–18 अंकी खाते क्रमांक',
        'ifsc': 'IFSC कोड',
        'ifsc_ph': 'उदा.: SBIN0001234',
        'tracking_title': '📍 लाइव्ह शिपमेंट आणि प्रक्रिया ट्रॅकिंग',
        'tracking_sub': 'तुमचा खरेदीचा माल सध्या कुठे प्रक्रिया किंवा पाठवला जात आहे ते पाहा.',
        'tracking_token_ph': 'टोकन टाका, उदा. P101',
        'track_lot': 'माझा माल ट्रॅक करा',
        'tracking_empty': 'प्रथम शेतकरी नोंदणी करा, नंतर डिजिटल टोकन टाकून ट्रॅकिंग तपशील पाहा.',
        'tracking_id': 'ट्रॅकिंग ID',
        'current_stage': 'सध्याचा टप्पा',
        'current_location': 'सध्याचे ठिकाण',
        'last_gps': 'शेवटचे GPS अपडेट',
        'start_gps': '📡 GPS ट्रॅकिंग सुरू करा',
        'stop_gps': '⏹ GPS ट्रॅकिंग थांबवा',
        'simulate_stage': '🔄 पुढील टप्प्याचे सिम्युलेशन करा',
        'stage_centre': 'खरेदी केंद्रात',
        'stage_quality': 'गुणवत्ता तपासणी',
        'stage_weighing': 'वजन',
        'stage_processing': 'प्रक्रिया',
        'stage_shipped': 'पाठवले',
        'stage_transit': 'मार्गावर',
        'stage_delivered': 'वितरण पूर्ण',
        'loc_centre': 'खरेदी केंद्र',
        'loc_quality': 'गुणवत्ता तपासणी युनिट',
        'loc_weighing': 'वजन केंद्र',
        'loc_processing': 'प्रक्रिया युनिट',
        'loc_dispatch': 'डिस्पॅच केंद्र',
        'loc_live': 'लाइव्ह GPS ठिकाण',
        'loc_destination': 'गंतव्य केंद्र',
        'gps_active': '🟢 GPS ट्रॅकिंग सुरू आहे आणि ठिकाणाचे अपडेट पाठवले जात आहेत.',
        'gps_stopped': 'GPS ट्रॅकिंग सध्या बंद आहे.',
        'gps_permission': '📡 GPS परवानगी मागितली जात आहे...',
        'gps_live': '🟢 GPS लाइव्ह • अचूकता ±{accuracy} मी • शेवटचे अपडेट {time}',
        'gps_error': 'GPS त्रुटी: {message}',
        'gps_update_error': 'GPS अपडेट त्रुटी: {message}',
        'tracking_not_found': 'ट्रॅकिंग रेकॉर्ड सापडला नाही',
        'valid_token': 'P101 सारखे वैध टोकन टाका.',
        'load_token_first': 'प्रथम ट्रॅकिंग टोकन लोड करा.',
        'gps_unsupported': 'या ब्राउझरमध्ये GPS/जिओलोकेशन समर्थित नाही.',
        'lot_delivered': 'माल आधीच वितरित म्हणून चिन्हांकित आहे.',
        'tracking_load_error': 'ट्रॅकिंग तपशील लोड करता आला नाही.',
        'tracking_update_error': 'ट्रॅकिंग टप्पा अपडेट करता आला नाही.',
        'tracking_id_success': ' ट्रॅकिंग ID: {tracking_id}.',
        'valid_mobile': 'कृपया वैध 10 अंकी मोबाइल नंबर टाका.',
        'valid_account': 'कृपया वैध 9–18 अंकी बँक खाते क्रमांक टाका.',
        'valid_ifsc': 'कृपया वैध 11-अक्षरी IFSC कोड टाका.'},
 'gu': {'bank_title': '🏦 બેંક વિગતો',
        'bank_help': 'પારદર્શક ચુકવણી પ્રક્રિયા માટે ખેડૂતની બેંક વિગતો ઉમેરો.',
        'bank_name': 'બેંકનું નામ',
        'bank_name_ph': 'ઉદાહરણ: સ્ટેટ બેંક ઓફ ઈન્ડિયા',
        'account_holder': 'ખાતાધારકનું નામ',
        'account_holder_ph': 'બેંક ખાતા મુજબ',
        'account_number': 'ખાતા નંબર',
        'account_number_ph': '9–18 અંકનો ખાતા નંબર',
        'ifsc': 'IFSC કોડ',
        'ifsc_ph': 'ઉદાહરણ: SBIN0001234',
        'tracking_title': '📍 લાઇવ શિપમેન્ટ અને પ્રોસેસિંગ ટ્રેકિંગ',
        'tracking_sub': 'તમારો ખરીદીનો માલ હાલમાં ક્યાં પ્રક્રિયા અથવા મોકલવામાં આવી રહ્યો છે તે જુઓ.',
        'tracking_token_ph': 'ટોકન દાખલ કરો, ઉદાહરણ P101',
        'track_lot': 'મારો માલ ટ્રેક કરો',
        'tracking_empty': 'પહેલા ખેડૂતની નોંધણી કરો, પછી ડિજિટલ ટોકન દાખલ કરીને ટ્રેકિંગ વિગતો જુઓ.',
        'tracking_id': 'ટ્રેકિંગ ID',
        'current_stage': 'હાલનો તબક્કો',
        'current_location': 'હાલનું સ્થાન',
        'last_gps': 'છેલ્લું GPS અપડેટ',
        'start_gps': '📡 GPS ટ્રેકિંગ શરૂ કરો',
        'stop_gps': '⏹ GPS ટ્રેકિંગ બંધ કરો',
        'simulate_stage': '🔄 આગળના તબક્કાનું સિમ્યુલેશન કરો',
        'stage_centre': 'ખરીદી કેન્દ્ર પર',
        'stage_quality': 'ગુણવત્તા તપાસ',
        'stage_weighing': 'વજન',
        'stage_processing': 'પ્રક્રિયા',
        'stage_shipped': 'મોકલવામાં આવ્યું',
        'stage_transit': 'માર્ગમાં',
        'stage_delivered': 'ડિલિવરી પૂર્ણ',
        'loc_centre': 'ખરીદી કેન્દ્ર',
        'loc_quality': 'ગુણવત્તા તપાસ એકમ',
        'loc_weighing': 'વજન કેન્દ્ર',
        'loc_processing': 'પ્રોસેસિંગ એકમ',
        'loc_dispatch': 'ડિસ્પેચ કેન્દ્ર',
        'loc_live': 'લાઇવ GPS સ્થાન',
        'loc_destination': 'ગંતવ્ય કેન્દ્ર',
        'gps_active': '🟢 GPS ટ્રેકિંગ સક્રિય છે અને સ્થાન અપડેટ મોકલાઈ રહ્યા છે.',
        'gps_stopped': 'GPS ટ્રેકિંગ હાલમાં બંધ છે.',
        'gps_permission': '📡 GPS પરવાનગી માંગવામાં આવી રહી છે...',
        'gps_live': '🟢 GPS લાઇવ • ચોકસાઈ ±{accuracy} મીટર • છેલ્લું અપડેટ {time}',
        'gps_error': 'GPS ભૂલ: {message}',
        'gps_update_error': 'GPS અપડેટ ભૂલ: {message}',
        'tracking_not_found': 'ટ્રેકિંગ રેકોર્ડ મળ્યો નથી',
        'valid_token': 'P101 જેવા માન્ય ટોકન દાખલ કરો.',
        'load_token_first': 'પહેલા ટ્રેકિંગ ટોકન લોડ કરો.',
        'gps_unsupported': 'આ બ્રાઉઝરમાં GPS/જિયોલોકેશન સપોર્ટેડ નથી.',
        'lot_delivered': 'માલ પહેલેથી ડિલિવર થયેલ તરીકે ચિહ્નિત છે.',
        'tracking_load_error': 'ટ્રેકિંગ વિગતો લોડ થઈ શકી નથી.',
        'tracking_update_error': 'ટ્રેકિંગ તબક્કો અપડેટ થઈ શક્યો નથી.',
        'tracking_id_success': ' ટ્રેકિંગ ID: {tracking_id}.',
        'valid_mobile': 'કૃપા કરીને માન્ય 10 અંકનો મોબાઇલ નંબર દાખલ કરો.',
        'valid_account': 'કૃપા કરીને માન્ય 9–18 અંકનો બેંક ખાતા નંબર દાખલ કરો.',
        'valid_ifsc': 'કૃપા કરીને માન્ય 11 અક્ષરનો IFSC કોડ દાખલ કરો.'},
 'kn': {'bank_title': '🏦 ಬ್ಯಾಂಕ್ ವಿವರಗಳು',
        'bank_help': 'ಪಾರದರ್ಶಕ ಪಾವತಿ ಪ್ರಕ್ರಿಯೆಗಾಗಿ ರೈತರ ಬ್ಯಾಂಕ್ ವಿವರಗಳನ್ನು ಸೇರಿಸಿ.',
        'bank_name': 'ಬ್ಯಾಂಕ್ ಹೆಸರು',
        'bank_name_ph': 'ಉದಾ: ಸ್ಟೇಟ್ ಬ್ಯಾಂಕ್ ಆಫ್ ಇಂಡಿಯಾ',
        'account_holder': 'ಖಾತೆದಾರರ ಹೆಸರು',
        'account_holder_ph': 'ಬ್ಯಾಂಕ್ ಖಾತೆಯಲ್ಲಿರುವಂತೆ',
        'account_number': 'ಖಾತೆ ಸಂಖ್ಯೆ',
        'account_number_ph': '9–18 ಅಂಕೆಗಳ ಖಾತೆ ಸಂಖ್ಯೆ',
        'ifsc': 'IFSC ಕೋಡ್',
        'ifsc_ph': 'ಉದಾ: SBIN0001234',
        'tracking_title': '📍 ಲೈವ್ ಶಿಪ್\u200cಮೆಂಟ್ ಮತ್ತು ಪ್ರೊಸೆಸಿಂಗ್ ಟ್ರ್ಯಾಕಿಂಗ್',
        'tracking_sub': 'ನಿಮ್ಮ ಖರೀದಿ ಸರಕು ಪ್ರಸ್ತುತ ಎಲ್ಲಿದೆ ಮತ್ತು ಎಲ್ಲಿ ಪ್ರಕ್ರಿಯೆಗೊಳ್ಳುತ್ತಿದೆ ಅಥವಾ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ ನೋಡಿ.',
        'tracking_token_ph': 'ಟೋಕನ್ ನಮೂದಿಸಿ, ಉದಾ. P101',
        'track_lot': 'ನನ್ನ ಸರಕನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ',
        'tracking_empty': 'ಮೊದಲು ರೈತರ ನೋಂದಣಿ ಮಾಡಿ, ನಂತರ ಡಿಜಿಟಲ್ ಟೋಕನ್ ನಮೂದಿಸಿ ಟ್ರ್ಯಾಕಿಂಗ್ ವಿವರಗಳನ್ನು ನೋಡಿ.',
        'tracking_id': 'ಟ್ರ್ಯಾಕಿಂಗ್ ID',
        'current_stage': 'ಪ್ರಸ್ತುತ ಹಂತ',
        'current_location': 'ಪ್ರಸ್ತುತ ಸ್ಥಳ',
        'last_gps': 'ಕೊನೆಯ GPS ನವೀಕರಣ',
        'start_gps': '📡 GPS ಟ್ರ್ಯಾಕಿಂಗ್ ಪ್ರಾರಂಭಿಸಿ',
        'stop_gps': '⏹ GPS ಟ್ರ್ಯಾಕಿಂಗ್ ನಿಲ್ಲಿಸಿ',
        'simulate_stage': '🔄 ಮುಂದಿನ ಹಂತವನ್ನು ಸಿಮ್ಯುಲೇಟ್ ಮಾಡಿ',
        'stage_centre': 'ಖರೀದಿ ಕೇಂದ್ರದಲ್ಲಿ',
        'stage_quality': 'ಗುಣಮಟ್ಟ ಪರಿಶೀಲನೆ',
        'stage_weighing': 'ತೂಕ',
        'stage_processing': 'ಸಂಸ್ಕರಣೆ',
        'stage_shipped': 'ಕಳುಹಿಸಲಾಗಿದೆ',
        'stage_transit': 'ಸಾಗಣೆಯಲ್ಲಿದೆ',
        'stage_delivered': 'ವಿತರಿಸಲಾಗಿದೆ',
        'loc_centre': 'ಖರೀದಿ ಕೇಂದ್ರ',
        'loc_quality': 'ಗುಣಮಟ್ಟ ಪರಿಶೀಲನಾ ಘಟಕ',
        'loc_weighing': 'ತೂಕ ಕೇಂದ್ರ',
        'loc_processing': 'ಸಂಸ್ಕರಣಾ ಘಟಕ',
        'loc_dispatch': 'ಡಿಸ್ಪ್ಯಾಚ್ ಕೇಂದ್ರ',
        'loc_live': 'ಲೈವ್ GPS ಸ್ಥಳ',
        'loc_destination': 'ಗಮ್ಯಸ್ಥಾನ ಕೇಂದ್ರ',
        'gps_active': '🟢 GPS ಟ್ರ್ಯಾಕಿಂಗ್ ಸಕ್ರಿಯವಾಗಿದೆ ಮತ್ತು ಸ್ಥಳದ ನವೀಕರಣಗಳನ್ನು ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ.',
        'gps_stopped': 'GPS ಟ್ರ್ಯಾಕಿಂಗ್ ಪ್ರಸ್ತುತ ನಿಂತಿದೆ.',
        'gps_permission': '📡 GPS ಅನುಮತಿ ಕೇಳಲಾಗುತ್ತಿದೆ...',
        'gps_live': '🟢 GPS ಲೈವ್ • ನಿಖರತೆ ±{accuracy} ಮೀ • ಕೊನೆಯ ನವೀಕರಣ {time}',
        'gps_error': 'GPS ದೋಷ: {message}',
        'gps_update_error': 'GPS ನವೀಕರಣ ದೋಷ: {message}',
        'tracking_not_found': 'ಟ್ರ್ಯಾಕಿಂಗ್ ದಾಖಲೆ ಕಂಡುಬಂದಿಲ್ಲ',
        'valid_token': 'P101 ನಂತಹ ಮಾನ್ಯ ಟೋಕನ್ ನಮೂದಿಸಿ.',
        'load_token_first': 'ಮೊದಲು ಟ್ರ್ಯಾಕಿಂಗ್ ಟೋಕನ್ ಲೋಡ್ ಮಾಡಿ.',
        'gps_unsupported': 'ಈ ಬ್ರೌಸರ್\u200cನಲ್ಲಿ GPS/ಜಿಯೋಲೊಕೇಶನ್ ಬೆಂಬಲಿತವಲ್ಲ.',
        'lot_delivered': 'ಸರಕು ಈಗಾಗಲೇ ವಿತರಿಸಲಾಗಿದೆ ಎಂದು ಗುರುತಿಸಲಾಗಿದೆ.',
        'tracking_load_error': 'ಟ್ರ್ಯಾಕಿಂಗ್ ವಿವರಗಳನ್ನು ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.',
        'tracking_update_error': 'ಟ್ರ್ಯಾಕಿಂಗ್ ಹಂತವನ್ನು ನವೀಕರಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.',
        'tracking_id_success': ' ಟ್ರ್ಯಾಕಿಂಗ್ ID: {tracking_id}.',
        'valid_mobile': 'ದಯವಿಟ್ಟು ಮಾನ್ಯ 10 ಅಂಕೆಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.',
        'valid_account': 'ದಯವಿಟ್ಟು ಮಾನ್ಯ 9–18 ಅಂಕೆಗಳ ಬ್ಯಾಂಕ್ ಖಾತೆ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.',
        'valid_ifsc': 'ದಯವಿಟ್ಟು ಮಾನ್ಯ 11 ಅಕ್ಷರಗಳ IFSC ಕೋಡ್ ನಮೂದಿಸಿ.'},
 'ml': {'bank_title': '🏦 ബാങ്ക് വിവരങ്ങൾ',
        'bank_help': 'സുതാര്യമായ പേയ്മെന്റ് പ്രക്രിയയ്ക്കായി കർഷകന്റെ ബാങ്ക് വിവരങ്ങൾ ചേർക്കുക.',
        'bank_name': 'ബാങ്കിന്റെ പേര്',
        'bank_name_ph': 'ഉദാ: സ്റ്റേറ്റ് ബാങ്ക് ഓഫ് ഇന്ത്യ',
        'account_holder': 'അക്കൗണ്ട് ഉടമയുടെ പേര്',
        'account_holder_ph': 'ബാങ്ക് അക്കൗണ്ടിലുള്ളത് പോലെ',
        'account_number': 'അക്കൗണ്ട് നമ്പർ',
        'account_number_ph': '9–18 അക്ക അക്കൗണ്ട് നമ്പർ',
        'ifsc': 'IFSC കോഡ്',
        'ifsc_ph': 'ഉദാ: SBIN0001234',
        'tracking_title': '📍 ലൈവ് ഷിപ്പ്മെന്റ് & പ്രോസസ്സിംഗ് ട്രാക്കിംഗ്',
        'tracking_sub': 'നിങ്ങളുടെ സംഭരണ ലോട്ട് ഇപ്പോൾ എവിടെയാണ് പ്രോസസ്സ് ചെയ്യുന്നത് അല്ലെങ്കിൽ അയയ്ക്കുന്നത് എന്ന് കാണുക.',
        'tracking_token_ph': 'ടോക്കൺ നൽകുക, ഉദാ. P101',
        'track_lot': 'എന്റെ ലോട്ട് ട്രാക്ക് ചെയ്യുക',
        'tracking_empty': 'ആദ്യം കർഷകനെ രജിസ്റ്റർ ചെയ്യുക, തുടർന്ന് ഡിജിറ്റൽ ടോക്കൺ നൽകി ട്രാക്കിംഗ് വിവരങ്ങൾ കാണുക.',
        'tracking_id': 'ട്രാക്കിംഗ് ID',
        'current_stage': 'നിലവിലെ ഘട്ടം',
        'current_location': 'നിലവിലെ സ്ഥലം',
        'last_gps': 'അവസാന GPS അപ്ഡേറ്റ്',
        'start_gps': '📡 GPS ട്രാക്കിംഗ് ആരംഭിക്കുക',
        'stop_gps': '⏹ GPS ട്രാക്കിംഗ് നിർത്തുക',
        'simulate_stage': '🔄 അടുത്ത ഘട്ടം സിമുലേറ്റ് ചെയ്യുക',
        'stage_centre': 'വാങ്ങൽ കേന്ദ്രത്തിൽ',
        'stage_quality': 'ഗുണനിലവാര പരിശോധന',
        'stage_weighing': 'തൂക്കം',
        'stage_processing': 'പ്രോസസ്സിംഗ്',
        'stage_shipped': 'അയച്ചു',
        'stage_transit': 'യാത്രയിലാണ്',
        'stage_delivered': 'ഡെലിവറി പൂർത്തിയായി',
        'loc_centre': 'വാങ്ങൽ കേന്ദ്രം',
        'loc_quality': 'ഗുണനിലവാര പരിശോധന യൂണിറ്റ്',
        'loc_weighing': 'തൂക്ക കേന്ദ്രം',
        'loc_processing': 'പ്രോസസ്സിംഗ് യൂണിറ്റ്',
        'loc_dispatch': 'ഡിസ്പാച്ച് കേന്ദ്രം',
        'loc_live': 'ലൈവ് GPS സ്ഥലം',
        'loc_destination': 'ലക്ഷ്യ കേന്ദ്രം',
        'gps_active': '🟢 GPS ട്രാക്കിംഗ് സജീവമാണ്, സ്ഥല അപ്ഡേറ്റുകൾ അയയ്ക്കുന്നു.',
        'gps_stopped': 'GPS ട്രാക്കിംഗ് ഇപ്പോൾ നിർത്തിയിരിക്കുന്നു.',
        'gps_permission': '📡 GPS അനുമതി അഭ്യർത്ഥിക്കുന്നു...',
        'gps_live': '🟢 GPS ലൈവ് • കൃത്യത ±{accuracy} മീ • അവസാന അപ്ഡേറ്റ് {time}',
        'gps_error': 'GPS പിശക്: {message}',
        'gps_update_error': 'GPS അപ്ഡേറ്റ് പിശക്: {message}',
        'tracking_not_found': 'ട്രാക്കിംഗ് റെക്കോർഡ് കണ്ടെത്താനായില്ല',
        'valid_token': 'P101 പോലുള്ള സാധുവായ ടോക്കൺ നൽകുക.',
        'load_token_first': 'ആദ്യം ഒരു ട്രാക്കിംഗ് ടോക്കൺ ലോഡ് ചെയ്യുക.',
        'gps_unsupported': 'ഈ ബ്രൗസറിൽ GPS/ജിയോലൊക്കേഷൻ പിന്തുണയ്ക്കുന്നില്ല.',
        'lot_delivered': 'ലോട്ട് ഇതിനകം ഡെലിവർ ചെയ്തതായി അടയാളപ്പെടുത്തിയിരിക്കുന്നു.',
        'tracking_load_error': 'ട്രാക്കിംഗ് വിവരങ്ങൾ ലോഡ് ചെയ്യാനായില്ല.',
        'tracking_update_error': 'ട്രാക്കിംഗ് ഘട്ടം അപ്ഡേറ്റ് ചെയ്യാനായില്ല.',
        'tracking_id_success': ' ട്രാക്കിംഗ് ID: {tracking_id}.',
        'valid_mobile': 'സാധുവായ 10 അക്ക മൊബൈൽ നമ്പർ നൽകുക.',
        'valid_account': 'സാധുവായ 9–18 അക്ക ബാങ്ക് അക്കൗണ്ട് നമ്പർ നൽകുക.',
        'valid_ifsc': 'സാധുവായ 11 അക്ഷര IFSC കോഡ് നൽകുക.'},
 'or': {'bank_title': '🏦 ବ୍ୟାଙ୍କ ବିବରଣୀ',
        'bank_help': 'ସ୍ୱଚ୍ଛ ପେମେଣ୍ଟ ପ୍ରକ୍ରିୟା ପାଇଁ ଚାଷୀଙ୍କ ବ୍ୟାଙ୍କ ବିବରଣୀ ଯୋଡନ୍ତୁ।',
        'bank_name': 'ବ୍ୟାଙ୍କ ନାମ',
        'bank_name_ph': 'ଉଦାହରଣ: ଷ୍ଟେଟ୍ ବ୍ୟାଙ୍କ ଅଫ୍ ଇଣ୍ଡିଆ',
        'account_holder': 'ଖାତାଧାରୀଙ୍କ ନାମ',
        'account_holder_ph': 'ବ୍ୟାଙ୍କ ଖାତା ଅନୁଯାୟୀ',
        'account_number': 'ଖାତା ନମ୍ବର',
        'account_number_ph': '୯–୧୮ ଅଙ୍କର ଖାତା ନମ୍ବର',
        'ifsc': 'IFSC କୋଡ୍',
        'ifsc_ph': 'ଉଦାହରଣ: SBIN0001234',
        'tracking_title': '📍 ଲାଇଭ୍ ଶିପମେଣ୍ଟ ଏବଂ ପ୍ରକ୍ରିୟା ଟ୍ରାକିଂ',
        'tracking_sub': 'ଆପଣଙ୍କ କ୍ରୟ ସାମଗ୍ରୀ ବର୍ତ୍ତମାନ କେଉଁଠାରେ ପ୍ରକ୍ରିୟା କିମ୍ବା ପଠାଯାଉଛି ଦେଖନ୍ତୁ।',
        'tracking_token_ph': 'ଟୋକେନ୍ ଦିଅନ୍ତୁ, ଯଥା P101',
        'track_lot': 'ମୋ ସାମଗ୍ରୀ ଟ୍ରାକ୍ କରନ୍ତୁ',
        'tracking_empty': 'ପ୍ରଥମେ ଚାଷୀ ପଞ୍ଜୀକରଣ କରନ୍ତୁ, ପରେ ଡିଜିଟାଲ୍ ଟୋକେନ୍ ଦେଇ ଟ୍ରାକିଂ ବିବରଣୀ ଦେଖନ୍ତୁ।',
        'tracking_id': 'ଟ୍ରାକିଂ ID',
        'current_stage': 'ବର୍ତ୍ତମାନ ପର୍ଯ୍ୟାୟ',
        'current_location': 'ବର୍ତ୍ତମାନ ସ୍ଥାନ',
        'last_gps': 'ଶେଷ GPS ଅପଡେଟ୍',
        'start_gps': '📡 GPS ଟ୍ରାକିଂ ଆରମ୍ଭ କରନ୍ତୁ',
        'stop_gps': '⏹ GPS ଟ୍ରାକିଂ ବନ୍ଦ କରନ୍ତୁ',
        'simulate_stage': '🔄 ପରବର୍ତ୍ତୀ ପର୍ଯ୍ୟାୟ ସିମୁଲେଟ୍ କରନ୍ତୁ',
        'stage_centre': 'କ୍ରୟ କେନ୍ଦ୍ରରେ',
        'stage_quality': 'ଗୁଣବତ୍ତା ଯାଞ୍ଚ',
        'stage_weighing': 'ଓଜନ',
        'stage_processing': 'ପ୍ରକ୍ରିୟାକରଣ',
        'stage_shipped': 'ପଠାଯାଇଛି',
        'stage_transit': 'ପଥରେ',
        'stage_delivered': 'ଡେଲିଭରି ସମ୍ପୂର୍ଣ୍ଣ',
        'loc_centre': 'କ୍ରୟ କେନ୍ଦ୍ର',
        'loc_quality': 'ଗୁଣବତ୍ତା ଯାଞ୍ଚ ୟୁନିଟ୍',
        'loc_weighing': 'ଓଜନ କେନ୍ଦ୍ର',
        'loc_processing': 'ପ୍ରକ୍ରିୟାକରଣ ୟୁନିଟ୍',
        'loc_dispatch': 'ଡିସ୍ପାଚ୍ କେନ୍ଦ୍ର',
        'loc_live': 'ଲାଇଭ୍ GPS ସ୍ଥାନ',
        'loc_destination': 'ଗନ୍ତବ୍ୟ କେନ୍ଦ୍ର',
        'gps_active': '🟢 GPS ଟ୍ରାକିଂ ସକ୍ରିୟ ଅଛି ଏବଂ ସ୍ଥାନ ଅପଡେଟ୍ ପଠାଯାଉଛି।',
        'gps_stopped': 'GPS ଟ୍ରାକିଂ ବର୍ତ୍ତମାନ ବନ୍ଦ ଅଛି।',
        'gps_permission': '📡 GPS ଅନୁମତି ମଗାଯାଉଛି...',
        'gps_live': '🟢 GPS ଲାଇଭ୍ • ସଠିକତା ±{accuracy} ମି • ଶେଷ ଅପଡେଟ୍ {time}',
        'gps_error': 'GPS ତ୍ରୁଟି: {message}',
        'gps_update_error': 'GPS ଅପଡେଟ୍ ତ୍ରୁଟି: {message}',
        'tracking_not_found': 'ଟ୍ରାକିଂ ରେକର୍ଡ ମିଳିଲା ନାହିଁ',
        'valid_token': 'P101 ପରି ଏକ ବୈଧ ଟୋକେନ୍ ଦିଅନ୍ତୁ।',
        'load_token_first': 'ପ୍ରଥମେ ଏକ ଟ୍ରାକିଂ ଟୋକେନ୍ ଲୋଡ୍ କରନ୍ତୁ।',
        'gps_unsupported': 'ଏହି ବ୍ରାଉଜରରେ GPS/ଜିଓଲୋକେସନ୍ ସମର୍ଥିତ ନୁହେଁ।',
        'lot_delivered': 'ସାମଗ୍ରୀ ପୂର୍ବରୁ ଡେଲିଭର୍ ହୋଇଛି ବୋଲି ଚିହ୍ନିତ।',
        'tracking_load_error': 'ଟ୍ରାକିଂ ବିବରଣୀ ଲୋଡ୍ ହୋଇପାରିଲା ନାହିଁ।',
        'tracking_update_error': 'ଟ୍ରାକିଂ ପର୍ଯ୍ୟାୟ ଅପଡେଟ୍ ହୋଇପାରିଲା ନାହିଁ।',
        'tracking_id_success': ' ଟ୍ରାକିଂ ID: {tracking_id}.',
        'valid_mobile': 'ଦୟାକରି ଏକ ବୈଧ ୧୦ ଅଙ୍କର ମୋବାଇଲ୍ ନମ୍ବର ଦିଅନ୍ତୁ।',
        'valid_account': 'ଦୟାକରି ଏକ ବୈଧ ୯–୧୮ ଅଙ୍କର ବ୍ୟାଙ୍କ ଖାତା ନମ୍ବର ଦିଅନ୍ତୁ।',
        'valid_ifsc': 'ଦୟାକରି ଏକ ବୈଧ ୧୧ ଅକ୍ଷରର IFSC କୋଡ୍ ଦିଅନ୍ତୁ।'},
 'pa': {'bank_title': '🏦 ਬੈਂਕ ਵੇਰਵੇ',
        'bank_help': 'ਪਾਰਦਰਸ਼ੀ ਭੁਗਤਾਨ ਪ੍ਰਕਿਰਿਆ ਲਈ ਕਿਸਾਨ ਦੇ ਬੈਂਕ ਵੇਰਵੇ ਸ਼ਾਮਲ ਕਰੋ।',
        'bank_name': 'ਬੈਂਕ ਦਾ ਨਾਮ',
        'bank_name_ph': 'ਉਦਾਹਰਨ: ਸਟੇਟ ਬੈਂਕ ਆਫ ਇੰਡੀਆ',
        'account_holder': 'ਖਾਤਾ ਧਾਰਕ ਦਾ ਨਾਮ',
        'account_holder_ph': 'ਬੈਂਕ ਖਾਤੇ ਅਨੁਸਾਰ',
        'account_number': 'ਖਾਤਾ ਨੰਬਰ',
        'account_number_ph': '9–18 ਅੰਕਾਂ ਦਾ ਖਾਤਾ ਨੰਬਰ',
        'ifsc': 'IFSC ਕੋਡ',
        'ifsc_ph': 'ਉਦਾਹਰਨ: SBIN0001234',
        'tracking_title': '📍 ਲਾਈਵ ਸ਼ਿਪਮੈਂਟ ਅਤੇ ਪ੍ਰੋਸੈਸਿੰਗ ਟ੍ਰੈਕਿੰਗ',
        'tracking_sub': 'ਵੇਖੋ ਕਿ ਤੁਹਾਡੀ ਖਰੀਦ ਦੀ ਖੇਪ ਇਸ ਵੇਲੇ ਕਿੱਥੇ ਪ੍ਰੋਸੈਸ ਜਾਂ ਭੇਜੀ ਜਾ ਰਹੀ ਹੈ।',
        'tracking_token_ph': 'ਟੋਕਨ ਦਰਜ ਕਰੋ, ਜਿਵੇਂ P101',
        'track_lot': 'ਮੇਰੀ ਖੇਪ ਟ੍ਰੈਕ ਕਰੋ',
        'tracking_empty': 'ਪਹਿਲਾਂ ਕਿਸਾਨ ਰਜਿਸਟਰ ਕਰੋ, ਫਿਰ ਡਿਜ਼ਿਟਲ ਟੋਕਨ ਦਰਜ ਕਰਕੇ ਟ੍ਰੈਕਿੰਗ ਵੇਰਵੇ ਵੇਖੋ।',
        'tracking_id': 'ਟ੍ਰੈਕਿੰਗ ID',
        'current_stage': 'ਮੌਜੂਦਾ ਪੜਾਅ',
        'current_location': 'ਮੌਜੂਦਾ ਸਥਾਨ',
        'last_gps': 'ਆਖਰੀ GPS ਅਪਡੇਟ',
        'start_gps': '📡 GPS ਟ੍ਰੈਕਿੰਗ ਸ਼ੁਰੂ ਕਰੋ',
        'stop_gps': '⏹ GPS ਟ੍ਰੈਕਿੰਗ ਬੰਦ ਕਰੋ',
        'simulate_stage': '🔄 ਅਗਲੇ ਪੜਾਅ ਦੀ ਸਿਮੂਲੇਸ਼ਨ ਕਰੋ',
        'stage_centre': "ਖਰੀਦ ਕੇਂਦਰ 'ਤੇ",
        'stage_quality': 'ਗੁਣਵੱਤਾ ਜਾਂਚ',
        'stage_weighing': 'ਤੋਲ',
        'stage_processing': 'ਪ੍ਰੋਸੈਸਿੰਗ',
        'stage_shipped': 'ਭੇਜਿਆ ਗਿਆ',
        'stage_transit': 'ਰਸਤੇ ਵਿੱਚ',
        'stage_delivered': 'ਡਿਲੀਵਰੀ ਪੂਰੀ',
        'loc_centre': 'ਖਰੀਦ ਕੇਂਦਰ',
        'loc_quality': 'ਗੁਣਵੱਤਾ ਜਾਂਚ ਯੂਨਿਟ',
        'loc_weighing': 'ਤੋਲ ਕੇਂਦਰ',
        'loc_processing': 'ਪ੍ਰੋਸੈਸਿੰਗ ਯੂਨਿਟ',
        'loc_dispatch': 'ਡਿਸਪੈਚ ਕੇਂਦਰ',
        'loc_live': 'ਲਾਈਵ GPS ਸਥਾਨ',
        'loc_destination': 'ਮੰਜ਼ਿਲ ਕੇਂਦਰ',
        'gps_active': '🟢 GPS ਟ੍ਰੈਕਿੰਗ ਚਾਲੂ ਹੈ ਅਤੇ ਸਥਾਨ ਦੇ ਅਪਡੇਟ ਭੇਜੇ ਜਾ ਰਹੇ ਹਨ।',
        'gps_stopped': 'GPS ਟ੍ਰੈਕਿੰਗ ਇਸ ਵੇਲੇ ਬੰਦ ਹੈ।',
        'gps_permission': '📡 GPS ਦੀ ਇਜਾਜ਼ਤ ਮੰਗੀ ਜਾ ਰਹੀ ਹੈ...',
        'gps_live': '🟢 GPS ਲਾਈਵ • ਸਹੀਤਾ ±{accuracy} ਮੀਟਰ • ਆਖਰੀ ਅਪਡੇਟ {time}',
        'gps_error': 'GPS ਗਲਤੀ: {message}',
        'gps_update_error': 'GPS ਅਪਡੇਟ ਗਲਤੀ: {message}',
        'tracking_not_found': 'ਟ੍ਰੈਕਿੰਗ ਰਿਕਾਰਡ ਨਹੀਂ ਮਿਲਿਆ',
        'valid_token': 'P101 ਵਰਗਾ ਵੈਧ ਟੋਕਨ ਦਰਜ ਕਰੋ।',
        'load_token_first': 'ਪਹਿਲਾਂ ਟ੍ਰੈਕਿੰਗ ਟੋਕਨ ਲੋਡ ਕਰੋ।',
        'gps_unsupported': 'ਇਸ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ GPS/ਜਿਓਲੋਕੇਸ਼ਨ ਸਮਰਥਿਤ ਨਹੀਂ ਹੈ।',
        'lot_delivered': 'ਖੇਪ ਨੂੰ ਪਹਿਲਾਂ ਹੀ ਡਿਲੀਵਰ ਵਜੋਂ ਦਰਜ ਕੀਤਾ ਗਿਆ ਹੈ।',
        'tracking_load_error': 'ਟ੍ਰੈਕਿੰਗ ਵੇਰਵੇ ਲੋਡ ਨਹੀਂ ਹੋ ਸਕੇ।',
        'tracking_update_error': 'ਟ੍ਰੈਕਿੰਗ ਪੜਾਅ ਅਪਡੇਟ ਨਹੀਂ ਹੋ ਸਕਿਆ।',
        'tracking_id_success': ' ਟ੍ਰੈਕਿੰਗ ID: {tracking_id}.',
        'valid_mobile': 'ਕਿਰਪਾ ਕਰਕੇ ਵੈਧ 10 ਅੰਕਾਂ ਦਾ ਮੋਬਾਈਲ ਨੰਬਰ ਦਰਜ ਕਰੋ।',
        'valid_account': 'ਕਿਰਪਾ ਕਰਕੇ ਵੈਧ 9–18 ਅੰਕਾਂ ਦਾ ਬੈਂਕ ਖਾਤਾ ਨੰਬਰ ਦਰਜ ਕਰੋ।',
        'valid_ifsc': 'ਕਿਰਪਾ ਕਰਕੇ ਵੈਧ 11 ਅੱਖਰਾਂ ਦਾ IFSC ਕੋਡ ਦਰਜ ਕਰੋ।'}}
for _code, _vals in _NEW_FEATURE_TRANSLATIONS.items():
    TRANSLATIONS[_code].update(_vals)

# ---------------- FARMER EFFORT / LOT TRACE / EXPLAINABLE REJECTION TRANSLATIONS ----------------
_ADDED_FEATURE_TEXT = {
    "en": {
        "effort_title":"👨‍🌾 Farmer Effort Index", "effort_desc":"Measures unnecessary visits, waiting time and repeated processes to reduce the hidden burden on farmers.",
        "effort_visits":"Centre visits", "effort_unnecessary":"Unnecessary visits", "effort_wait":"Waiting time", "effort_repeat":"Repeated processes", "effort_score":"Effort Index", "effort_record_visit":"Record Centre Visit", "effort_score_help":"Higher score means lower measured burden.", "effort_no_data":"Enter a token to view the Farmer Effort Index.",
        "lot_title":"🔗 Lot Trace", "lot_desc":"Digital trail for every procurement lot from farmer → quality check → procurement → payment.", "lot_farmer":"Farmer Registration", "lot_quality":"Quality Check", "lot_procurement":"Procurement", "lot_payment":"Payment", "lot_pending":"Pending", "lot_completed":"Completed", "lot_rejected":"Rejected", "lot_update":"Update Lot Step", "lot_step_help":"Use the controls to record each completed procurement step.",
        "rejection_title":"📝 Explainable Rejection", "rejection_desc":"Record the specific rejection reason and actionable guidance for the farmer's next attempt.", "rejection_reason":"Rejection Reason", "rejection_guidance":"Actionable Guidance", "rejection_select":"Select a reason", "rejection_save":"Save Rejection", "rejection_none":"No rejection has been recorded for this lot.", "rejection_saved":"Rejection recorded successfully.", "rejection_required":"Select a rejection reason and add guidance.", "rejection_quality":"Quality does not meet required grade", "rejection_moisture":"Moisture level is above the allowed limit", "rejection_impurity":"Excess impurities or foreign material", "rejection_damage":"Damaged, spoiled or pest-affected produce", "rejection_quantity":"Quantity/packaging mismatch", "rejection_other":"Other quality issue"
    },
    "hi": {
        "effort_title":"👨‍🌾 किसान प्रयास सूचकांक", "effort_desc":"अनावश्यक यात्राओं, प्रतीक्षा समय और दोहराई गई प्रक्रियाओं को मापकर किसानों का छिपा बोझ कम करने में मदद करता है।", "effort_visits":"केंद्र की यात्राएं", "effort_unnecessary":"अनावश्यक यात्राएं", "effort_wait":"प्रतीक्षा समय", "effort_repeat":"दोहराई गई प्रक्रियाएं", "effort_score":"प्रयास सूचकांक", "effort_record_visit":"केंद्र की यात्रा दर्ज करें", "effort_score_help":"अधिक स्कोर का अर्थ कम मापा गया बोझ है।", "effort_no_data":"किसान प्रयास सूचकांक देखने के लिए टोकन दर्ज करें।",
        "lot_title":"🔗 लॉट ट्रेस", "lot_desc":"हर खरीद लॉट का डिजिटल रिकॉर्ड किसान → गुणवत्ता जांच → खरीद → भुगतान तक।", "lot_farmer":"किसान पंजीकरण", "lot_quality":"गुणवत्ता जांच", "lot_procurement":"खरीद", "lot_payment":"भुगतान", "lot_pending":"लंबित", "lot_completed":"पूरा", "lot_rejected":"अस्वीकृत", "lot_update":"लॉट चरण अपडेट करें", "lot_step_help":"हर पूरी हुई खरीद प्रक्रिया को दर्ज करने के लिए नियंत्रणों का उपयोग करें।",
        "rejection_title":"📝 अस्वीकृति का स्पष्ट कारण", "rejection_desc":"अस्वीकृति का कारण दर्ज करें और किसान की अगली कोशिश के लिए उपयोगी मार्गदर्शन दें।", "rejection_reason":"अस्वीकृति का कारण", "rejection_guidance":"उपयोगी मार्गदर्शन", "rejection_select":"कारण चुनें", "rejection_save":"अस्वीकृति सहेजें", "rejection_none":"इस लॉट के लिए कोई अस्वीकृति दर्ज नहीं है।", "rejection_saved":"अस्वीकृति सफलतापूर्वक दर्ज की गई।", "rejection_required":"अस्वीकृति का कारण चुनें और मार्गदर्शन लिखें।", "rejection_quality":"गुणवत्ता आवश्यक ग्रेड के अनुरूप नहीं", "rejection_moisture":"नमी निर्धारित सीमा से अधिक", "rejection_impurity":"अधिक अशुद्धियां या बाहरी सामग्री", "rejection_damage":"उत्पाद क्षतिग्रस्त, खराब या कीट प्रभावित", "rejection_quantity":"मात्रा/पैकेजिंग में असंगति", "rejection_other":"अन्य गुणवत्ता समस्या"
    },
    "bn": {
        "effort_title":"👨‍🌾 কৃষক প্রচেষ্টা সূচক", "effort_desc":"অপ্রয়োজনীয় যাতায়াত, অপেক্ষার সময় ও পুনরাবৃত্ত প্রক্রিয়া মেপে কৃষকের অদৃশ্য চাপ কমাতে সাহায্য করে।", "effort_visits":"কেন্দ্রে যাতায়াত", "effort_unnecessary":"অপ্রয়োজনীয় যাতায়াত", "effort_wait":"অপেক্ষার সময়", "effort_repeat":"পুনরাবৃত্ত প্রক্রিয়া", "effort_score":"প্রচেষ্টা সূচক", "effort_record_visit":"কেন্দ্রে যাতায়াত রেকর্ড করুন", "effort_score_help":"স্কোর বেশি হলে মাপা চাপ কম।", "effort_no_data":"কৃষক প্রচেষ্টা সূচক দেখতে টোকেন দিন।",
        "lot_title":"🔗 লট ট্রেস", "lot_desc":"কৃষক → মান পরীক্ষা → ক্রয় → পেমেন্ট পর্যন্ত প্রতিটি ক্রয় লটের ডিজিটাল রেকর্ড।", "lot_farmer":"কৃষক নিবন্ধন", "lot_quality":"মান পরীক্ষা", "lot_procurement":"ক্রয়", "lot_payment":"পেমেন্ট", "lot_pending":"অপেক্ষমাণ", "lot_completed":"সম্পন্ন", "lot_rejected":"প্রত্যাখ্যাত", "lot_update":"লট ধাপ আপডেট করুন", "lot_step_help":"সম্পন্ন ক্রয় ধাপ রেকর্ড করতে নিয়ন্ত্রণ ব্যবহার করুন।",
        "rejection_title":"📝 ব্যাখ্যাযোগ্য প্রত্যাখ্যান", "rejection_desc":"প্রত্যাখ্যানের নির্দিষ্ট কারণ ও পরবর্তী প্রচেষ্টার জন্য কার্যকর পরামর্শ রেকর্ড করুন।", "rejection_reason":"প্রত্যাখ্যানের কারণ", "rejection_guidance":"কার্যকর পরামর্শ", "rejection_select":"কারণ নির্বাচন করুন", "rejection_save":"প্রত্যাখ্যান সংরক্ষণ করুন", "rejection_none":"এই লটের জন্য কোনো প্রত্যাখ্যান রেকর্ড নেই।", "rejection_saved":"প্রত্যাখ্যান সফলভাবে রেকর্ড হয়েছে।", "rejection_required":"কারণ নির্বাচন করুন এবং পরামর্শ লিখুন।", "rejection_quality":"গুণমান প্রয়োজনীয় গ্রেড পূরণ করে না", "rejection_moisture":"আর্দ্রতা অনুমোদিত সীমার বেশি", "rejection_impurity":"অতিরিক্ত অমেধ্য বা বিদেশি উপাদান", "rejection_damage":"ক্ষতিগ্রস্ত, নষ্ট বা পোকায় আক্রান্ত পণ্য", "rejection_quantity":"পরিমাণ/প্যাকেজিং অসামঞ্জস্য", "rejection_other":"অন্যান্য গুণগত সমস্যা"
    },
    "ta": {
        "effort_title":"👨‍🌾 விவசாயி முயற்சி குறியீடு", "effort_desc":"தேவையற்ற வருகைகள், காத்திருப்பு நேரம் மற்றும் மீண்டும் செய்யப்படும் செயல்முறைகளை அளவிடுகிறது.", "effort_visits":"மைய வருகைகள்", "effort_unnecessary":"தேவையற்ற வருகைகள்", "effort_wait":"காத்திருப்பு நேரம்", "effort_repeat":"மீண்டும் செய்யப்பட்ட செயல்முறைகள்", "effort_score":"முயற்சி குறியீடு", "effort_record_visit":"மைய வருகையை பதிவு செய்க", "effort_score_help":"அதிக மதிப்பெண் குறைந்த அளவிடப்பட்ட சுமையை குறிக்கிறது.", "effort_no_data":"முயற்சி குறியீட்டை பார்க்க டோக்கனை உள்ளிடவும்.",
        "lot_title":"🔗 லாட் தடம்", "lot_desc":"விவசாயி → தரச் சோதனை → கொள்முதல் → பணம் வரை ஒவ்வொரு லாட்டிற்கும் டிஜிட்டல் தடம்.", "lot_farmer":"விவசாயி பதிவு", "lot_quality":"தரச் சோதனை", "lot_procurement":"கொள்முதல்", "lot_payment":"பணம்", "lot_pending":"நிலுவை", "lot_completed":"முடிந்தது", "lot_rejected":"நிராகரிக்கப்பட்டது", "lot_update":"லாட் நிலையை புதுப்பிக்கவும்", "lot_step_help":"முடிந்த கொள்முதல் படிகளை பதிவு செய்ய கட்டுப்பாடுகளைப் பயன்படுத்தவும்.",
        "rejection_title":"📝 விளக்கத்துடன் நிராகரிப்பு", "rejection_desc":"நிராகரிப்பிற்கான குறிப்பிட்ட காரணத்தையும் அடுத்த முயற்சிக்கான வழிகாட்டுதலையும் பதிவு செய்யவும்.", "rejection_reason":"நிராகரிப்பு காரணம்", "rejection_guidance":"வழிகாட்டுதல்", "rejection_select":"காரணத்தைத் தேர்ந்தெடுக்கவும்", "rejection_save":"நிராகரிப்பை சேமிக்கவும்", "rejection_none":"இந்த லாட்டிற்கு நிராகரிப்பு பதிவு செய்யப்படவில்லை.", "rejection_saved":"நிராகரிப்பு வெற்றிகரமாக பதிவு செய்யப்பட்டது.", "rejection_required":"காரணத்தைத் தேர்ந்தெடுத்து வழிகாட்டுதலை உள்ளிடவும்.", "rejection_quality":"தரம் தேவையான அளவை பூர்த்தி செய்யவில்லை", "rejection_moisture":"ஈரப்பதம் அனுமதிக்கப்பட்ட அளவை விட அதிகம்", "rejection_impurity":"அதிக அசுத்தங்கள் அல்லது வெளிப்பொருள்", "rejection_damage":"சேதமடைந்த அல்லது பூச்சி பாதித்த விளைபொருள்", "rejection_quantity":"அளவு/பேக்கேஜிங் பொருந்தவில்லை", "rejection_other":"பிற தரப் பிரச்சினை"
    },
    "as": {
        "effort_title":"👨‍🌾 কৃষক প্ৰচেষ্টা সূচক", "effort_desc":"অপ্ৰয়োজনীয় যাত্ৰা, অপেক্ষাৰ সময় আৰু পুনৰাবৃত্ত প্ৰক্ৰিয়া জুখি কৃষকৰ অদৃশ্য বোজা কমাবলৈ সহায় কৰে।", "effort_visits":"কেন্দ্ৰলৈ যাত্ৰা", "effort_unnecessary":"অপ্ৰয়োজনীয় যাত্ৰা", "effort_wait":"অপেক্ষাৰ সময়", "effort_repeat":"পুনৰাবৃত্ত প্ৰক্ৰিয়া", "effort_score":"প্ৰচেষ্টা সূচক", "effort_record_visit":"কেন্দ্ৰলৈ যাত্ৰা ৰেকৰ্ড কৰক", "effort_score_help":"বেছি স্ক’ৰে কম মাপ কৰা বোজা বুজায়।", "effort_no_data":"প্ৰচেষ্টা সূচক চাবলৈ টোকেন দিয়ক।",
        "lot_title":"🔗 লট ট্ৰেচ", "lot_desc":"কৃষক → গুণগত পৰীক্ষা → ক্ৰয় → পেমেণ্টলৈ প্ৰতিটো ক্ৰয় লটৰ ডিজিটেল ট্ৰেইল।", "lot_farmer":"কৃষক পঞ্জীয়ন", "lot_quality":"গুণগত পৰীক্ষা", "lot_procurement":"ক্ৰয়", "lot_payment":"পেমেণ্ট", "lot_pending":"বাকী", "lot_completed":"সম্পূৰ্ণ", "lot_rejected":"প্ৰত্যাখ্যান", "lot_update":"লটৰ ধাপ আপডেট কৰক", "lot_step_help":"সম্পূৰ্ণ ক্ৰয় ধাপ ৰেকৰ্ড কৰিবলৈ নিয়ন্ত্ৰণ ব্যৱহাৰ কৰক।",
        "rejection_title":"📝 ব্যাখ্যাযোগ্য প্ৰত্যাখ্যান", "rejection_desc":"প্ৰত্যাখ্যানৰ নিৰ্দিষ্ট কাৰণ আৰু পৰৱৰ্তী চেষ্টাৰ বাবে ব্যৱহাৰিক পৰামৰ্শ ৰেকৰ্ড কৰক।", "rejection_reason":"প্ৰত্যাখ্যানৰ কাৰণ", "rejection_guidance":"ব্যৱহাৰিক পৰামৰ্শ", "rejection_select":"কাৰণ বাছনি কৰক", "rejection_save":"প্ৰত্যাখ্যান সংৰক্ষণ কৰক", "rejection_none":"এই লটৰ বাবে কোনো প্ৰত্যাখ্যান ৰেকৰ্ড কৰা হোৱা নাই।", "rejection_saved":"প্ৰত্যাখ্যান সফলভাৱে ৰেকৰ্ড কৰা হৈছে।", "rejection_required":"কাৰণ বাছনি কৰি পৰামৰ্শ লিখক।", "rejection_quality":"গুণগত মান প্ৰয়োজনীয় গ্ৰেডৰ নহয়", "rejection_moisture":"আৰ্দ্ৰতা অনুমোদিত সীমাতকৈ বেছি", "rejection_impurity":"অতিৰিক্ত অশুদ্ধি বা বাহিৰা পদাৰ্থ", "rejection_damage":"ক্ষতিগ্ৰস্ত, নষ্ট বা কীট-পতংগ আক্ৰান্ত উৎপাদন", "rejection_quantity":"পৰিমাণ/পেকেজিংৰ অমিল", "rejection_other":"অন্য গুণগত সমস্যা"
    },
    "te": {
        "effort_title":"👨‍🌾 రైతు ప్రయత్న సూచిక", "effort_desc":"అవసరం లేని సందర్శనలు, వేచి ఉండే సమయం మరియు పునరావృత ప్రక్రియలను కొలుస్తుంది.", "effort_visits":"కేంద్ర సందర్శనలు", "effort_unnecessary":"అనవసర సందర్శనలు", "effort_wait":"వేచి ఉన్న సమయం", "effort_repeat":"పునరావృత ప్రక్రియలు", "effort_score":"ప్రయత్న సూచిక", "effort_record_visit":"కేంద్ర సందర్శన నమోదు", "effort_score_help":"ఎక్కువ స్కోరు అంటే కొలిచిన భారం తక్కువ.", "effort_no_data":"ప్రయత్న సూచిక కోసం టోకెన్ నమోదు చేయండి.",
        "lot_title":"🔗 లాట్ ట్రేస్", "lot_desc":"రైతు → నాణ్యత తనిఖీ → కొనుగోలు → చెల్లింపు వరకు ప్రతి లాట్‌కు డిజిటల్ ట్రయిల్.", "lot_farmer":"రైతు నమోదు", "lot_quality":"నాణ్యత తనిఖీ", "lot_procurement":"కొనుగోలు", "lot_payment":"చెల్లింపు", "lot_pending":"పెండింగ్", "lot_completed":"పూర్తయింది", "lot_rejected":"తిరస్కరించబడింది", "lot_update":"లాట్ దశను నవీకరించండి", "lot_step_help":"పూర్తైన కొనుగోలు దశలను నమోదు చేయడానికి నియంత్రణలను ఉపయోగించండి.",
        "rejection_title":"📝 కారణంతో తిరస్కరణ", "rejection_desc":"తిరస్కరణకు కారణం మరియు తదుపరి ప్రయత్నానికి ఉపయోగకరమైన మార్గదర్శకాన్ని నమోదు చేయండి.", "rejection_reason":"తిరస్కరణ కారణం", "rejection_guidance":"మార్గదర్శకం", "rejection_select":"కారణాన్ని ఎంచుకోండి", "rejection_save":"తిరస్కరణను సేవ్ చేయండి", "rejection_none":"ఈ లాట్‌కు తిరస్కరణ నమోదు కాలేదు.", "rejection_saved":"తిరస్కరణ విజయవంతంగా నమోదు అయింది.", "rejection_required":"కారణాన్ని ఎంచుకుని మార్గదర్శకం నమోదు చేయండి.", "rejection_quality":"నాణ్యత అవసరమైన గ్రేడ్‌కు సరిపోలలేదు", "rejection_moisture":"తేమ అనుమతించిన పరిమితి కంటే ఎక్కువ", "rejection_impurity":"అధిక మలినాలు లేదా విదేశీ పదార్థం", "rejection_damage":"దెబ్బతిన్న, చెడిపోయిన లేదా పురుగు ప్రభావిత పంట", "rejection_quantity":"పరిమాణం/ప్యాకేజింగ్ సరిపోలలేదు", "rejection_other":"ఇతర నాణ్యత సమస్య"
    },
    "mr": {
        "effort_title":"👨‍🌾 शेतकरी प्रयत्न निर्देशांक", "effort_desc":"अनावश्यक भेटी, प्रतीक्षा वेळ आणि पुन्हा होणाऱ्या प्रक्रिया मोजून शेतकऱ्यांवरील लपलेला भार कमी करण्यास मदत करतो.", "effort_visits":"केंद्र भेटी", "effort_unnecessary":"अनावश्यक भेटी", "effort_wait":"प्रतीक्षा वेळ", "effort_repeat":"पुनरावृत्ती प्रक्रिया", "effort_score":"प्रयत्न निर्देशांक", "effort_record_visit":"केंद्र भेट नोंदवा", "effort_score_help":"जास्त गुण म्हणजे मोजलेला भार कमी.", "effort_no_data":"प्रयत्न निर्देशांक पाहण्यासाठी टोकन द्या.",
        "lot_title":"🔗 लॉट ट्रेस", "lot_desc":"शेतकरी → गुणवत्ता तपासणी → खरेदी → पेमेंटपर्यंत प्रत्येक लॉटचा डिजिटल मागोवा.", "lot_farmer":"शेतकरी नोंदणी", "lot_quality":"गुणवत्ता तपासणी", "lot_procurement":"खरेदी", "lot_payment":"पेमेंट", "lot_pending":"प्रलंबित", "lot_completed":"पूर्ण", "lot_rejected":"नाकारले", "lot_update":"लॉट टप्पा अपडेट करा", "lot_step_help":"पूर्ण झालेल्या खरेदी टप्प्यांची नोंद करण्यासाठी नियंत्रण वापरा.",
        "rejection_title":"📝 स्पष्ट कारणासह नकार", "rejection_desc":"नकाराचे विशिष्ट कारण आणि पुढील प्रयत्नासाठी उपयुक्त मार्गदर्शन नोंदवा.", "rejection_reason":"नकाराचे कारण", "rejection_guidance":"मार्गदर्शन", "rejection_select":"कारण निवडा", "rejection_save":"नकार जतन करा", "rejection_none":"या लॉटसाठी कोणताही नकार नोंदवलेला नाही.", "rejection_saved":"नकार यशस्वीपणे नोंदवला.", "rejection_required":"नकाराचे कारण निवडा आणि मार्गदर्शन लिहा.", "rejection_quality":"गुणवत्ता आवश्यक श्रेणीची नाही", "rejection_moisture":"ओलावा अनुमत मर्यादेपेक्षा जास्त", "rejection_impurity":"जास्त अशुद्धता किंवा परकीय पदार्थ", "rejection_damage":"नुकसान झालेले, खराब किंवा किडीग्रस्त उत्पादन", "rejection_quantity":"प्रमाण/पॅकेजिंग विसंगत", "rejection_other":"इतर गुणवत्ता समस्या"
    },
    "gu": {
        "effort_title":"👨‍🌾 ખેડૂત પ્રયત્ન સૂચકાંક", "effort_desc":"બિનજરૂરી મુલાકાતો, રાહ જોવાનો સમય અને પુનરાવર્તિત પ્રક્રિયાઓ માપે છે.", "effort_visits":"કેન્દ્ર મુલાકાતો", "effort_unnecessary":"બિનજરૂરી મુલાકાતો", "effort_wait":"રાહ સમય", "effort_repeat":"પુનરાવર્તિત પ્રક્રિયાઓ", "effort_score":"પ્રયત્ન સૂચકાંક", "effort_record_visit":"કેન્દ્ર મુલાકાત નોંધો", "effort_score_help":"વધુ સ્કોર એટલે માપાયેલ ભાર ઓછો.", "effort_no_data":"પ્રયત્ન સૂચકાંક જોવા ટોકન દાખલ કરો.",
        "lot_title":"🔗 લોટ ટ્રેસ", "lot_desc":"ખેડૂત → ગુણવત્તા તપાસ → ખરીદી → ચુકવણી સુધી દરેક લોટનો ડિજિટલ ટ્રેલ.", "lot_farmer":"ખેડૂત નોંધણી", "lot_quality":"ગુણવત્તા તપાસ", "lot_procurement":"ખરીદી", "lot_payment":"ચુકવણી", "lot_pending":"બાકી", "lot_completed":"પૂર્ણ", "lot_rejected":"નકારાયેલ", "lot_update":"લોટનો તબક્કો અપડેટ કરો", "lot_step_help":"પૂર્ણ થયેલા ખરીદીના તબક્કા નોંધવા નિયંત્રણો વાપરો.",
        "rejection_title":"📝 સમજાવી શકાય એવો નકાર", "rejection_desc":"નકારનું ચોક્કસ કારણ અને આગામી પ્રયાસ માટે ઉપયોગી માર્ગદર્શન નોંધો.", "rejection_reason":"નકારનું કારણ", "rejection_guidance":"માર્ગદર્શન", "rejection_select":"કારણ પસંદ કરો", "rejection_save":"નકાર સાચવો", "rejection_none":"આ લોટ માટે કોઈ નકાર નોંધાયેલ નથી.", "rejection_saved":"નકાર સફળતાપૂર્વક નોંધાયો.", "rejection_required":"કારણ પસંદ કરો અને માર્ગદર્શન ઉમેરો.", "rejection_quality":"ગુણવત્તા જરૂરી ગ્રેડ મુજબ નથી", "rejection_moisture":"ભેજ મંજૂર મર્યાદા કરતાં વધુ", "rejection_impurity":"વધુ અશુદ્ધિ અથવા વિદેશી સામગ્રી", "rejection_damage":"નુકસાન થયેલ, બગડેલ અથવા જીવાતથી અસરગ્રસ્ત ઉત્પાદન", "rejection_quantity":"જથ્થો/પેકેજિંગ અસંગત", "rejection_other":"અન્ય ગુણવત્તા સમસ્યા"
    },
    "kn": {
        "effort_title":"👨‍🌾 ರೈತ ಪ್ರಯತ್ನ ಸೂಚ್ಯಂಕ", "effort_desc":"ಅನಗತ್ಯ ಭೇಟಿಗಳು, ಕಾಯುವ ಸಮಯ ಮತ್ತು ಪುನರಾವರ್ತಿತ ಪ್ರಕ್ರಿಯೆಗಳನ್ನು ಅಳೆಯುತ್ತದೆ.", "effort_visits":"ಕೇಂದ್ರ ಭೇಟಿಗಳು", "effort_unnecessary":"ಅನಗತ್ಯ ಭೇಟಿಗಳು", "effort_wait":"ಕಾಯುವ ಸಮಯ", "effort_repeat":"ಪುನರಾವರ್ತಿತ ಪ್ರಕ್ರಿಯೆಗಳು", "effort_score":"ಪ್ರಯತ್ನ ಸೂಚ್ಯಂಕ", "effort_record_visit":"ಕೇಂದ್ರ ಭೇಟಿ ದಾಖಲಿಸಿ", "effort_score_help":"ಹೆಚ್ಚಿನ ಅಂಕ ಎಂದರೆ ಅಳೆಯಲಾದ ಹೊರೆ ಕಡಿಮೆ.", "effort_no_data":"ಪ್ರಯತ್ನ ಸೂಚ್ಯಂಕ ನೋಡಲು ಟೋಕನ್ ನಮೂದಿಸಿ.",
        "lot_title":"🔗 ಲಾಟ್ ಟ್ರೇಸ್", "lot_desc":"ರೈತ → ಗುಣಮಟ್ಟ ಪರಿಶೀಲನೆ → ಖರೀದಿ → ಪಾವತಿ ತನಕ ಪ್ರತಿ ಲಾಟ್‌ನ ಡಿಜಿಟಲ್ ಟ್ರೇಲ್.", "lot_farmer":"ರೈತ ನೋಂದಣಿ", "lot_quality":"ಗುಣಮಟ್ಟ ಪರಿಶೀಲನೆ", "lot_procurement":"ಖರೀದಿ", "lot_payment":"ಪಾವತಿ", "lot_pending":"ಬಾಕಿ", "lot_completed":"ಪೂರ್ಣ", "lot_rejected":"ತಿರಸ್ಕರಿಸಲಾಗಿದೆ", "lot_update":"ಲಾಟ್ ಹಂತವನ್ನು ನವೀಕರಿಸಿ", "lot_step_help":"ಪೂರ್ಣಗೊಂಡ ಖರೀದಿ ಹಂತಗಳನ್ನು ದಾಖಲಿಸಲು ನಿಯಂತ್ರಣಗಳನ್ನು ಬಳಸಿ.",
        "rejection_title":"📝 ವಿವರವಾದ ತಿರಸ್ಕರಣೆ", "rejection_desc":"ತಿರಸ್ಕರಣೆಯ ನಿರ್ದಿಷ್ಟ ಕಾರಣ ಮತ್ತು ಮುಂದಿನ ಪ್ರಯತ್ನಕ್ಕೆ ಉಪಯುಕ್ತ ಮಾರ್ಗದರ್ಶನ ದಾಖಲಿಸಿ.", "rejection_reason":"ತಿರಸ್ಕರಣೆಯ ಕಾರಣ", "rejection_guidance":"ಮಾರ್ಗದರ್ಶನ", "rejection_select":"ಕಾರಣ ಆಯ್ಕೆಮಾಡಿ", "rejection_save":"ತಿರಸ್ಕರಣೆಯನ್ನು ಉಳಿಸಿ", "rejection_none":"ಈ ಲಾಟ್‌ಗೆ ಯಾವುದೇ ತಿರಸ್ಕರಣೆ ದಾಖಲಾಗಿಲ್ಲ.", "rejection_saved":"ತಿರಸ್ಕರಣೆ ಯಶಸ್ವಿಯಾಗಿ ದಾಖಲಾಗಿದೆ.", "rejection_required":"ಕಾರಣ ಆಯ್ಕೆಮಾಡಿ ಮತ್ತು ಮಾರ್ಗದರ್ಶನ ನಮೂದಿಸಿ.", "rejection_quality":"ಗುಣಮಟ್ಟ ಅಗತ್ಯ ಗ್ರೇಡ್‌ಗೆ ಹೊಂದಿಕೆಯಾಗಿಲ್ಲ", "rejection_moisture":"ತೇವಾಂಶ ಅನುಮತಿತ ಮಿತಿಗಿಂತ ಹೆಚ್ಚು", "rejection_impurity":"ಹೆಚ್ಚಿನ ಅಶುದ್ಧತೆ ಅಥವಾ ಹೊರಗಿನ ವಸ್ತು", "rejection_damage":"ಹಾನಿಗೊಂಡ, ಹಾಳಾದ ಅಥವಾ ಕೀಟ ಬಾಧಿತ ಉತ್ಪನ್ನ", "rejection_quantity":"ಪ್ರಮಾಣ/ಪ್ಯಾಕೇಜಿಂಗ್ ಹೊಂದಿಕೆಯಾಗಿಲ್ಲ", "rejection_other":"ಇತರ ಗುಣಮಟ್ಟ ಸಮಸ್ಯೆ"
    },
    "ml": {
        "effort_title":"👨‍🌾 കർഷക ശ്രമ സൂചിക", "effort_desc":"അനാവശ്യ സന്ദർശനങ്ങൾ, കാത്തിരിപ്പ് സമയം, ആവർത്തിച്ചുള്ള പ്രക്രിയകൾ എന്നിവ അളക്കുന്നു.", "effort_visits":"കേന്ദ്ര സന്ദർശനങ്ങൾ", "effort_unnecessary":"അനാവശ്യ സന്ദർശനങ്ങൾ", "effort_wait":"കാത്തിരിപ്പ് സമയം", "effort_repeat":"ആവർത്തിച്ച പ്രക്രിയകൾ", "effort_score":"ശ്രമ സൂചിക", "effort_record_visit":"കേന്ദ്ര സന്ദർശനം രേഖപ്പെടുത്തുക", "effort_score_help":"കൂടിയ സ്കോർ അളന്ന ഭാരം കുറവാണെന്ന് സൂചിപ്പിക്കുന്നു.", "effort_no_data":"ശ്രമ സൂചിക കാണാൻ ടോക്കൺ നൽകുക.",
        "lot_title":"🔗 ലോട്ട് ട്രേസ്", "lot_desc":"കർഷകൻ → ഗുണനിലവാര പരിശോധന → വാങ്ങൽ → പേയ്മെന്റ് വരെ ഓരോ ലോട്ടിന്റെയും ഡിജിറ്റൽ രേഖ.", "lot_farmer":"കർഷക രജിസ്ട്രേഷൻ", "lot_quality":"ഗുണനിലവാര പരിശോധന", "lot_procurement":"വാങ്ങൽ", "lot_payment":"പേയ്മെന്റ്", "lot_pending":"ബാക്കി", "lot_completed":"പൂർത്തിയായി", "lot_rejected":"നിരസിച്ചു", "lot_update":"ലോട്ട് ഘട്ടം അപ്ഡേറ്റ് ചെയ്യുക", "lot_step_help":"പൂർത്തിയായ വാങ്ങൽ ഘട്ടങ്ങൾ രേഖപ്പെടുത്താൻ നിയന്ത്രണങ്ങൾ ഉപയോഗിക്കുക.",
        "rejection_title":"📝 വിശദീകരിക്കാവുന്ന നിരസിക്കൽ", "rejection_desc":"നിരസിച്ചതിന്റെ കാരണംയും അടുത്ത ശ്രമത്തിനുള്ള പ്രായോഗിക മാർഗനിർദ്ദേശവും രേഖപ്പെടുത്തുക.", "rejection_reason":"നിരസിക്കാനുള്ള കാരണം", "rejection_guidance":"മാർഗനിർദ്ദേശം", "rejection_select":"കാരണം തിരഞ്ഞെടുക്കുക", "rejection_save":"നിരസിക്കൽ സംരക്ഷിക്കുക", "rejection_none":"ഈ ലോട്ടിന് നിരസിക്കൽ രേഖപ്പെടുത്തിയിട്ടില്ല.", "rejection_saved":"നിരസിക്കൽ വിജയകരമായി രേഖപ്പെടുത്തി.", "rejection_required":"കാരണം തിരഞ്ഞെടുക്കുകയും മാർഗനിർദ്ദേശം നൽകുകയും ചെയ്യുക.", "rejection_quality":"ഗുണനിലവാരം ആവശ്യമായ ഗ്രേഡിന് അനുയോജ്യമല്ല", "rejection_moisture":"ഈർപ്പം അനുവദനീയ പരിധിയേക്കാൾ കൂടുതലാണ്", "rejection_impurity":"അധിക മാലിന്യം അല്ലെങ്കിൽ വിദേശ വസ്തു", "rejection_damage":"കേടായ, നശിച്ച അല്ലെങ്കിൽ കീടബാധിത ഉൽപ്പന്നം", "rejection_quantity":"അളവ്/പാക്കേജിംഗ് പൊരുത്തപ്പെടുന്നില്ല", "rejection_other":"മറ്റ് ഗുണനിലവാര പ്രശ്നം"
    },
    "or": {
        "effort_title":"👨‍🌾 ଚାଷୀ ପ୍ରୟାସ ସୂଚକାଙ୍କ", "effort_desc":"ଅନାବଶ୍ୟକ ଯାତ୍ରା, ଅପେକ୍ଷା ସମୟ ଏବଂ ପୁନରାବୃତ୍ତ ପ୍ରକ୍ରିୟାକୁ ମାପେ।", "effort_visits":"କେନ୍ଦ୍ର ଯାତ୍ରା", "effort_unnecessary":"ଅନାବଶ୍ୟକ ଯାତ୍ରା", "effort_wait":"ଅପେକ୍ଷା ସମୟ", "effort_repeat":"ପୁନରାବୃତ୍ତ ପ୍ରକ୍ରିୟା", "effort_score":"ପ୍ରୟାସ ସୂଚକାଙ୍କ", "effort_record_visit":"କେନ୍ଦ୍ର ଯାତ୍ରା ରେକର୍ଡ କରନ୍ତୁ", "effort_score_help":"ଅଧିକ ସ୍କୋର ମାନେ ମାପାଯାଇଥିବା ଭାର କମ।", "effort_no_data":"ପ୍ରୟାସ ସୂଚକାଙ୍କ ଦେଖିବାକୁ ଟୋକେନ ଦିଅନ୍ତୁ।",
        "lot_title":"🔗 ଲଟ୍ ଟ୍ରେସ୍", "lot_desc":"ଚାଷୀ → ଗୁଣବତ୍ତା ଯାଞ୍ଚ → କ୍ରୟ → ପେମେଣ୍ଟ ପର୍ଯ୍ୟନ୍ତ ପ୍ରତ୍ୟେକ ଲଟ୍‌ର ଡିଜିଟାଲ୍ ରେକର୍ଡ।", "lot_farmer":"ଚାଷୀ ପଞ୍ଜୀକରଣ", "lot_quality":"ଗୁଣବତ୍ତା ଯାଞ୍ଚ", "lot_procurement":"କ୍ରୟ", "lot_payment":"ପେମେଣ୍ଟ", "lot_pending":"ବାକି", "lot_completed":"ସମ୍ପୂର୍ଣ୍ଣ", "lot_rejected":"ପ୍ରତ୍ୟାଖ୍ୟାନ", "lot_update":"ଲଟ୍ ପଦକ୍ଷେପ ଅପଡେଟ୍ କରନ୍ତୁ", "lot_step_help":"ସମ୍ପୂର୍ଣ୍ଣ କ୍ରୟ ପଦକ୍ଷେପ ରେକର୍ଡ କରିବାକୁ ନିୟନ୍ତ୍ରଣ ବ୍ୟବହାର କରନ୍ତୁ।",
        "rejection_title":"📝 ବ୍ୟାଖ୍ୟାଯୋଗ୍ୟ ପ୍ରତ୍ୟାଖ୍ୟାନ", "rejection_desc":"ପ୍ରତ୍ୟାଖ୍ୟାନର ନିର୍ଦ୍ଦିଷ୍ଟ କାରଣ ଏବଂ ପରବର୍ତ୍ତୀ ପ୍ରୟାସ ପାଇଁ ପ୍ରୟୋଗଯୋଗ୍ୟ ପରାମର୍ଶ ରେକର୍ଡ କରନ୍ତୁ।", "rejection_reason":"ପ୍ରତ୍ୟାଖ୍ୟାନର କାରଣ", "rejection_guidance":"ପରାମର୍ଶ", "rejection_select":"କାରଣ ବାଛନ୍ତୁ", "rejection_save":"ପ୍ରତ୍ୟାଖ୍ୟାନ ସଂରକ୍ଷଣ କରନ୍ତୁ", "rejection_none":"ଏହି ଲଟ୍ ପାଇଁ କୌଣସି ପ୍ରତ୍ୟାଖ୍ୟାନ ରେକର୍ଡ ହୋଇନାହିଁ।", "rejection_saved":"ପ୍ରତ୍ୟାଖ୍ୟାନ ସଫଳଭାବେ ରେକର୍ଡ ହୋଇଛି।", "rejection_required":"କାରଣ ବାଛନ୍ତୁ ଏବଂ ପରାମର୍ଶ ଲେଖନ୍ତୁ।", "rejection_quality":"ଗୁଣବତ୍ତା ଆବଶ୍ୟକ ଗ୍ରେଡ୍‌ର ନୁହେଁ", "rejection_moisture":"ଆର୍ଦ୍ରତା ଅନୁମୋଦିତ ସୀମାଠାରୁ ଅଧିକ", "rejection_impurity":"ଅତ୍ୟଧିକ ଅଶୁଦ୍ଧତା କିମ୍ବା ବିଦେଶୀ ପଦାର୍ଥ", "rejection_damage":"କ୍ଷତିଗ୍ରସ୍ତ, ନଷ୍ଟ କିମ୍ବା କୀଟ ପ୍ରଭାବିତ ଉତ୍ପାଦ", "rejection_quantity":"ପରିମାଣ/ପ୍ୟାକେଜିଂ ଅସଙ୍ଗତି", "rejection_other":"ଅନ୍ୟ ଗୁଣବତ୍ତା ସମସ୍ୟା"
    },
    "pa": {
        "effort_title":"👨‍🌾 ਕਿਸਾਨ ਯਤਨ ਸੂਚਕਾਂਕ", "effort_desc":"ਬੇਲੋੜੀਆਂ ਯਾਤਰਾਵਾਂ, ਉਡੀਕ ਸਮਾਂ ਅਤੇ ਦੁਹਰਾਈਆਂ ਪ੍ਰਕਿਰਿਆਵਾਂ ਨੂੰ ਮਾਪਦਾ ਹੈ।", "effort_visits":"ਕੇਂਦਰ ਦੌਰੇ", "effort_unnecessary":"ਬੇਲੋੜੇ ਦੌਰੇ", "effort_wait":"ਉਡੀਕ ਸਮਾਂ", "effort_repeat":"ਦੁਹਰਾਈਆਂ ਪ੍ਰਕਿਰਿਆਵਾਂ", "effort_score":"ਯਤਨ ਸੂਚਕਾਂਕ", "effort_record_visit":"ਕੇਂਦਰ ਦੌਰਾ ਦਰਜ ਕਰੋ", "effort_score_help":"ਵੱਧ ਸਕੋਰ ਦਾ ਮਤਲਬ ਮਾਪਿਆ ਗਿਆ ਬੋਝ ਘੱਟ ਹੈ।", "effort_no_data":"ਯਤਨ ਸੂਚਕਾਂਕ ਦੇਖਣ ਲਈ ਟੋਕਨ ਦਿਓ।",
        "lot_title":"🔗 ਲਾਟ ਟ੍ਰੇਸ", "lot_desc":"ਕਿਸਾਨ → ਗੁਣਵੱਤਾ ਜਾਂਚ → ਖਰੀਦ → ਭੁਗਤਾਨ ਤੱਕ ਹਰ ਲਾਟ ਦਾ ਡਿਜ਼ਿਟਲ ਟ੍ਰੇਲ।", "lot_farmer":"ਕਿਸਾਨ ਰਜਿਸਟ੍ਰੇਸ਼ਨ", "lot_quality":"ਗੁਣਵੱਤਾ ਜਾਂਚ", "lot_procurement":"ਖਰੀਦ", "lot_payment":"ਭੁਗਤਾਨ", "lot_pending":"ਬਕਾਇਆ", "lot_completed":"ਪੂਰਾ", "lot_rejected":"ਰੱਦ", "lot_update":"ਲਾਟ ਪੜਾਅ ਅਪਡੇਟ ਕਰੋ", "lot_step_help":"ਪੂਰੇ ਹੋਏ ਖਰੀਦ ਪੜਾਅ ਦਰਜ ਕਰਨ ਲਈ ਕੰਟਰੋਲ ਵਰਤੋ।",
        "rejection_title":"📝 ਵਿਆਖਿਆਯੋਗ ਰੱਦ", "rejection_desc":"ਰੱਦ ਕਰਨ ਦਾ ਖਾਸ ਕਾਰਨ ਅਤੇ ਅਗਲੀ ਕੋਸ਼ਿਸ਼ ਲਈ ਕਾਰਗਰ ਮਾਰਗਦਰਸ਼ਨ ਦਰਜ ਕਰੋ।", "rejection_reason":"ਰੱਦ ਕਰਨ ਦਾ ਕਾਰਨ", "rejection_guidance":"ਮਾਰਗਦਰਸ਼ਨ", "rejection_select":"ਕਾਰਨ ਚੁਣੋ", "rejection_save":"ਰੱਦਗੀ ਸੇਵ ਕਰੋ", "rejection_none":"ਇਸ ਲਾਟ ਲਈ ਕੋਈ ਰੱਦਗੀ ਦਰਜ ਨਹੀਂ ਹੈ।", "rejection_saved":"ਰੱਦਗੀ ਸਫਲਤਾਪੂਰਵਕ ਦਰਜ ਹੋ ਗਈ।", "rejection_required":"ਕਾਰਨ ਚੁਣੋ ਅਤੇ ਮਾਰਗਦਰਸ਼ਨ ਲਿਖੋ।", "rejection_quality":"ਗੁਣਵੱਤਾ ਲੋੜੀਂਦੇ ਗ੍ਰੇਡ ਅਨੁਸਾਰ ਨਹੀਂ", "rejection_moisture":"ਨਮੀ ਮਨਜ਼ੂਰ ਸੀਮਾ ਤੋਂ ਵੱਧ", "rejection_impurity":"ਵਾਧੂ ਅਸ਼ੁੱਧੀਆਂ ਜਾਂ ਬਾਹਰੀ ਸਮੱਗਰੀ", "rejection_damage":"ਨੁਕਸਾਨੀ, ਖਰਾਬ ਜਾਂ ਕੀੜਿਆਂ ਤੋਂ ਪ੍ਰਭਾਵਿਤ ਉਤਪਾਦ", "rejection_quantity":"ਮਾਤਰਾ/ਪੈਕੇਜਿੰਗ ਵਿੱਚ ਅਸੰਗਤਤਾ", "rejection_other":"ਹੋਰ ਗੁਣਵੱਤਾ ਸਮੱਸਿਆ"
    }
}
for _code, _vals in _ADDED_FEATURE_TEXT.items():
    TRANSLATIONS[_code].update(_vals)



# Login-page translations for all 12 supported languages.
LOGIN_TRANSLATIONS = {
    "en": {"title":"Welcome to KisanGati","sub":"Select your access type to continue.","farmer":"👨‍🌾 Farmer","admin":"🛡️ Admin","mobile":"Registered Mobile Number","mobile_ph":"10-digit mobile number","token":"Digital Token","token_ph":"e.g. P101","farmer_login":"Login as Farmer","new_farmer":"New Farmer? Register Here","farmer_note":"Farmers log in using the mobile number and digital token received after registration.","username":"Admin Username","username_ph":"Admin username","password":"Password","password_ph":"Admin password","admin_login":"Login as Admin","admin_note":"Admin access is for procurement centre staff and administrators.Admin Username for demo: admin Password: admin123","language":"Language","brand_desc":"Smart Agricultural Procurement & Farmer Assistance Platform","slot":"📅 Smart slot booking","queue":"🎟️ Digital token & live queue","tracking":"📍 Procurement & shipment tracking","payment":"💳 Transparent payment status","invalid_admin":"Invalid admin username or password.","invalid_farmer":"Invalid mobile number or digital token. If you are a new farmer, register first."},
    "hi": {"title":"KisanGati में आपका स्वागत है","sub":"जारी रखने के लिए अपना एक्सेस प्रकार चुनें।","farmer":"👨‍🌾 किसान","admin":"🛡️ एडमिन","mobile":"पंजीकृत मोबाइल नंबर","mobile_ph":"10 अंकों का मोबाइल नंबर","token":"डिजिटल टोकन","token_ph":"जैसे P101","farmer_login":"किसान के रूप में लॉगिन करें","new_farmer":"नए किसान? यहां पंजीकरण करें","farmer_note":"किसान पंजीकरण के बाद मिले मोबाइल नंबर और डिजिटल टोकन से लॉगिन कर सकते हैं।","username":"एडमिन यूज़रनेम","username_ph":"एडमिन यूज़रनेम","password":"पासवर्ड","password_ph":"एडमिन पासवर्ड","admin_login":"एडमिन के रूप में लॉगिन करें","admin_note":"एडमिन एक्सेस खरीद केंद्र के कर्मचारियों और प्रशासकों के लिए है।","language":"भाषा","brand_desc":"स्मार्ट कृषि खरीद और किसान सहायता प्लेटफ़ॉर्म","slot":"📅 स्मार्ट स्लॉट बुकिंग","queue":"🎟️ डिजिटल टोकन और लाइव कतार","tracking":"📍 खरीद और शिपमेंट ट्रैकिंग","payment":"💳 पारदर्शी भुगतान स्थिति","invalid_admin":"अमान्य एडमिन यूज़रनेम या पासवर्ड।","invalid_farmer":"अमान्य मोबाइल नंबर या डिजिटल टोकन। यदि आप नए किसान हैं, पहले पंजीकरण करें।"},
    "bn": {"title":"KisanGati-তে স্বাগতম","sub":"চালিয়ে যেতে আপনার অ্যাক্সেসের ধরন নির্বাচন করুন।","farmer":"👨‍🌾 কৃষক","admin":"🛡️ অ্যাডমিন","mobile":"নিবন্ধিত মোবাইল নম্বর","mobile_ph":"১০ সংখ্যার মোবাইল নম্বর","token":"ডিজিটাল টোকেন","token_ph":"যেমন P101","farmer_login":"কৃষক হিসেবে লগইন করুন","new_farmer":"নতুন কৃষক? এখানে নিবন্ধন করুন","farmer_note":"নিবন্ধনের পরে পাওয়া মোবাইল নম্বর ও ডিজিটাল টোকেন দিয়ে কৃষক লগইন করতে পারেন।","username":"অ্যাডমিন ইউজারনেম","username_ph":"অ্যাডমিন ইউজারনেম","password":"পাসওয়ার্ড","password_ph":"অ্যাডমিন পাসওয়ার্ড","admin_login":"অ্যাডমিন হিসেবে লগইন করুন","admin_note":"অ্যাডমিন অ্যাক্সেস ক্রয় কেন্দ্রের কর্মী ও প্রশাসকদের জন্য।","language":"ভাষা","brand_desc":"স্মার্ট কৃষি ক্রয় ও কৃষক সহায়তা প্ল্যাটফর্ম","slot":"📅 স্মার্ট স্লট বুকিং","queue":"🎟️ ডিজিটাল টোকেন ও লাইভ সারি","tracking":"📍 ক্রয় ও শিপমেন্ট ট্র্যাকিং","payment":"💳 স্বচ্ছ পেমেন্ট স্ট্যাটাস","invalid_admin":"অ্যাডমিন ইউজারনেম বা পাসওয়ার্ড ভুল।","invalid_farmer":"মোবাইল নম্বর বা ডিজিটাল টোকেন ভুল। নতুন কৃষক হলে আগে নিবন্ধন করুন।"},
    "ta": {"title":"KisanGati-க்கு வரவேற்கிறோம்","sub":"தொடர உங்கள் அணுகல் வகையைத் தேர்ந்தெடுக்கவும்.","farmer":"👨‍🌾 விவசாயி","admin":"🛡️ நிர்வாகி","mobile":"பதிவுசெய்யப்பட்ட மொபைல் எண்","mobile_ph":"10 இலக்க மொபைல் எண்","token":"டிஜிட்டல் டோக்கன்","token_ph":"எ.கா. P101","farmer_login":"விவசாயியாக உள்நுழைக","new_farmer":"புதிய விவசாயியா? இங்கே பதிவு செய்யவும்","farmer_note":"பதிவுக்குப் பிறகு கிடைத்த மொபைல் எண் மற்றும் டிஜிட்டல் டோக்கன் மூலம் விவசாயிகள் உள்நுழையலாம்.","username":"நிர்வாகி பயனர் பெயர்","username_ph":"நிர்வாகி பயனர் பெயர்","password":"கடவுச்சொல்","password_ph":"நிர்வாகி கடவுச்சொல்","admin_login":"நிர்வாகியாக உள்நுழைக","admin_note":"நிர்வாகி அணுகல் கொள்முதல் மைய ஊழியர்கள் மற்றும் நிர்வாகிகளுக்கானது.","language":"மொழி","brand_desc":"ஸ்மார்ட் வேளாண் கொள்முதல் மற்றும் விவசாயி உதவி தளம்","slot":"📅 ஸ்மார்ட் ஸ்லாட் முன்பதிவு","queue":"🎟️ டிஜிட்டல் டோக்கன் மற்றும் நேரடி வரிசை","tracking":"📍 கொள்முதல் மற்றும் அனுப்புதல் கண்காணிப்பு","payment":"💳 வெளிப்படையான பணப்பரிவர்த்தனை நிலை","invalid_admin":"நிர்வாகி பயனர் பெயர் அல்லது கடவுச்சொல் தவறானது.","invalid_farmer":"மொபைல் எண் அல்லது டிஜிட்டல் டோக்கன் தவறானது. புதிய விவசாயி என்றால் முதலில் பதிவு செய்யவும்."},
    "as": {"title":"KisanGati লৈ স্বাগতম","sub":"আগবাঢ়িবলৈ আপোনাৰ প্ৰৱেশৰ ধৰণ বাছনি কৰক।","farmer":"👨‍🌾 কৃষক","admin":"🛡️ প্ৰশাসক","mobile":"পঞ্জীয়ন কৰা মোবাইল নম্বৰ","mobile_ph":"১০ অংকৰ মোবাইল নম্বৰ","token":"ডিজিটেল টোকেন","token_ph":"যেনে P101","farmer_login":"কৃষক হিচাপে লগইন কৰক","new_farmer":"নতুন কৃষক? ইয়াত পঞ্জীয়ন কৰক","farmer_note":"পঞ্জীয়নৰ পিছত পোৱা মোবাইল নম্বৰ আৰু ডিজিটেল টোকেনেৰে কৃষকে লগইন কৰিব পাৰে।","username":"প্ৰশাসকৰ ইউজাৰনেম","username_ph":"প্ৰশাসকৰ ইউজাৰনেম","password":"পাছৱৰ্ড","password_ph":"প্ৰশাসকৰ পাছৱৰ্ড","admin_login":"প্ৰশাসক হিচাপে লগইন কৰক","admin_note":"প্ৰশাসক প্ৰৱেশ ক্ৰয় কেন্দ্ৰৰ কৰ্মচাৰী আৰু প্ৰশাসকৰ বাবে।","language":"ভাষা","brand_desc":"স্মাৰ্ট কৃষি ক্ৰয় আৰু কৃষক সহায়তা প্লেটফৰ্ম","slot":"📅 স্মাৰ্ট স্লট বুকিং","queue":"🎟️ ডিজিটেল টোকেন আৰু লাইভ শাৰী","tracking":"📍 ক্ৰয় আৰু শিপমেণ্ট ট্ৰেকিং","payment":"💳 স্বচ্ছ পেমেণ্টৰ অৱস্থা","invalid_admin":"প্ৰশাসকৰ ইউজাৰনেম বা পাছৱৰ্ড ভুল।","invalid_farmer":"মোবাইল নম্বৰ বা ডিজিটেল টোকেন ভুল। নতুন কৃষক হলে প্ৰথমে পঞ্জীয়ন কৰক।"},
    "te": {"title":"KisanGatiకి స్వాగతం","sub":"కొనసాగించడానికి మీ యాక్సెస్ రకాన్ని ఎంచుకోండి.","farmer":"👨‍🌾 రైతు","admin":"🛡️ నిర్వాహకుడు","mobile":"నమోదైన మొబైల్ నంబర్","mobile_ph":"10 అంకెల మొబైల్ నంబర్","token":"డిజిటల్ టోకెన్","token_ph":"ఉదా. P101","farmer_login":"రైతుగా లాగిన్ అవ్వండి","new_farmer":"కొత్త రైతా? ఇక్కడ నమోదు చేయండి","farmer_note":"నమోదు తర్వాత పొందిన మొబైల్ నంబర్ మరియు డిజిటల్ టోకెన్‌తో రైతులు లాగిన్ అవ్వవచ్చు.","username":"నిర్వాహక యూజర్‌నేమ్","username_ph":"నిర్వాహక యూజర్‌నేమ్","password":"పాస్‌వర్డ్","password_ph":"నిర్వాహక పాస్‌వర్డ్","admin_login":"నిర్వాహకుడిగా లాగిన్ అవ్వండి","admin_note":"నిర్వాహక యాక్సెస్ కొనుగోలు కేంద్ర సిబ్బంది మరియు నిర్వాహకుల కోసం.","language":"భాష","brand_desc":"స్మార్ట్ వ్యవసాయ కొనుగోలు మరియు రైతు సహాయ వేదిక","slot":"📅 స్మార్ట్ స్లాట్ బుకింగ్","queue":"🎟️ డిజిటల్ టోకెన్ & లైవ్ క్యూ","tracking":"📍 కొనుగోలు & షిప్‌మెంట్ ట్రాకింగ్","payment":"💳 పారదర్శక చెల్లింపు స్థితి","invalid_admin":"నిర్వాహక యూజర్‌నేమ్ లేదా పాస్‌వర్డ్ తప్పు.","invalid_farmer":"మొబైల్ నంబర్ లేదా డిజిటల్ టోకెన్ తప్పు. కొత్త రైతు అయితే ముందుగా నమోదు చేయండి."},
    "mr": {"title":"KisanGati मध्ये स्वागत आहे","sub":"पुढे जाण्यासाठी तुमचा प्रवेश प्रकार निवडा.","farmer":"👨‍🌾 शेतकरी","admin":"🛡️ प्रशासक","mobile":"नोंदणीकृत मोबाईल नंबर","mobile_ph":"10 अंकी मोबाईल नंबर","token":"डिजिटल टोकन","token_ph":"उदा. P101","farmer_login":"शेतकरी म्हणून लॉगिन करा","new_farmer":"नवीन शेतकरी? येथे नोंदणी करा","farmer_note":"नोंदणीनंतर मिळालेल्या मोबाईल नंबर आणि डिजिटल टोकनने शेतकरी लॉगिन करू शकतात.","username":"प्रशासक युजरनेम","username_ph":"प्रशासक युजरनेम","password":"पासवर्ड","password_ph":"प्रशासक पासवर्ड","admin_login":"प्रशासक म्हणून लॉगिन करा","admin_note":"प्रशासक प्रवेश खरेदी केंद्र कर्मचारी आणि प्रशासकांसाठी आहे.","language":"भाषा","brand_desc":"स्मार्ट कृषी खरेदी आणि शेतकरी सहाय्य प्लॅटफॉर्म","slot":"📅 स्मार्ट स्लॉट बुकिंग","queue":"🎟️ डिजिटल टोकन आणि लाइव्ह रांग","tracking":"📍 खरेदी आणि शिपमेंट ट्रॅकिंग","payment":"💳 पारदर्शक पेमेंट स्थिती","invalid_admin":"प्रशासक युजरनेम किंवा पासवर्ड चुकीचा आहे.","invalid_farmer":"मोबाईल नंबर किंवा डिजिटल टोकन चुकीचे आहे. नवीन शेतकरी असल्यास प्रथम नोंदणी करा."},
    "gu": {"title":"KisanGati માં આપનું સ્વાગત છે","sub":"આગળ વધવા માટે તમારો ઍક્સેસ પ્રકાર પસંદ કરો.","farmer":"👨‍🌾 ખેડૂત","admin":"🛡️ એડમિન","mobile":"નોંધાયેલ મોબાઇલ નંબર","mobile_ph":"10 અંકનો મોબાઇલ નંબર","token":"ડિજિટલ ટોકન","token_ph":"દા.ત. P101","farmer_login":"ખેડૂત તરીકે લોગિન કરો","new_farmer":"નવા ખેડૂત છો? અહીં નોંધણી કરો","farmer_note":"નોંધણી પછી મળેલા મોબાઇલ નંબર અને ડિજિટલ ટોકનથી ખેડૂત લોગિન કરી શકે છે.","username":"એડમિન યુઝરનેમ","username_ph":"એડમિન યુઝરનેમ","password":"પાસવર્ડ","password_ph":"એડમિન પાસવર્ડ","admin_login":"એડમિન તરીકે લોગિન કરો","admin_note":"એડમિન ઍક્સેસ ખરીદી કેન્દ્રના કર્મચારીઓ અને પ્રશાસકો માટે છે.","language":"ભાષા","brand_desc":"સ્માર્ટ કૃષિ ખરીદી અને ખેડૂત સહાય પ્લેટફોર્મ","slot":"📅 સ્માર્ટ સ્લોટ બુકિંગ","queue":"🎟️ ડિજિટલ ટોકન અને લાઇવ કતાર","tracking":"📍 ખરીદી અને શિપમેન્ટ ટ્રેકિંગ","payment":"💳 પારદર્શક ચુકવણી સ્થિતિ","invalid_admin":"એડમિન યુઝરનેમ અથવા પાસવર્ડ ખોટો છે.","invalid_farmer":"મોબાઇલ નંબર અથવા ડિજિટલ ટોકન ખોટું છે. નવા ખેડૂત હો તો પહેલા નોંધણી કરો."},
    "kn": {"title":"KisanGati ಗೆ ಸ್ವಾಗತ","sub":"ಮುಂದುವರಿಸಲು ನಿಮ್ಮ ಪ್ರವೇಶದ ಪ್ರಕಾರವನ್ನು ಆಯ್ಕೆಮಾಡಿ.","farmer":"👨‍🌾 ರೈತ","admin":"🛡️ ನಿರ್ವಾಹಕ","mobile":"ನೋಂದಾಯಿತ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ","mobile_ph":"10 ಅಂಕೆಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ","token":"ಡಿಜಿಟಲ್ ಟೋಕನ್","token_ph":"ಉದಾ. P101","farmer_login":"ರೈತರಾಗಿ ಲಾಗಿನ್ ಮಾಡಿ","new_farmer":"ಹೊಸ ರೈತರೇ? ಇಲ್ಲಿ ನೋಂದಣಿ ಮಾಡಿ","farmer_note":"ನೋಂದಣಿಯ ನಂತರ ಪಡೆದ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಮತ್ತು ಡಿಜಿಟಲ್ ಟೋಕನ್ ಬಳಸಿ ರೈತರು ಲಾಗಿನ್ ಮಾಡಬಹುದು.","username":"ನಿರ್ವಾಹಕ ಬಳಕೆದಾರ ಹೆಸರು","username_ph":"ನಿರ್ವಾಹಕ ಬಳಕೆದಾರ ಹೆಸರು","password":"ಪಾಸ್‌ವರ್ಡ್","password_ph":"ನಿರ್ವಾಹಕ ಪಾಸ್‌ವರ್ಡ್","admin_login":"ನಿರ್ವಾಹಕರಾಗಿ ಲಾಗಿನ್ ಮಾಡಿ","admin_note":"ನಿರ್ವಾಹಕ ಪ್ರವೇಶ ಖರೀದಿ ಕೇಂದ್ರದ ಸಿಬ್ಬಂದಿ ಮತ್ತು ನಿರ್ವಾಹಕರಿಗಾಗಿ.","language":"ಭಾಷೆ","brand_desc":"ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಖರೀದಿ ಮತ್ತು ರೈತ ಸಹಾಯ ವೇದಿಕೆ","slot":"📅 ಸ್ಮಾರ್ಟ್ ಸ್ಲಾಟ್ ಬುಕ್ಕಿಂಗ್","queue":"🎟️ ಡಿಜಿಟಲ್ ಟೋಕನ್ ಮತ್ತು ಲೈವ್ ಸರದಿ","tracking":"📍 ಖರೀದಿ ಮತ್ತು ಶಿಪ್‌ಮೆಂಟ್ ಟ್ರ್ಯಾಕಿಂಗ್","payment":"💳 ಪಾರದರ್ಶಕ ಪಾವತಿ ಸ್ಥಿತಿ","invalid_admin":"ನಿರ್ವಾಹಕ ಬಳಕೆದಾರ ಹೆಸರು ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್ ತಪ್ಪಾಗಿದೆ.","invalid_farmer":"ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಡಿಜಿಟಲ್ ಟೋಕನ್ ತಪ್ಪಾಗಿದೆ. ಹೊಸ ರೈತರಾದರೆ ಮೊದಲು ನೋಂದಣಿ ಮಾಡಿ."},
    "ml": {"title":"KisanGati-ലേക്ക് സ്വാഗതം","sub":"തുടരാൻ നിങ്ങളുടെ ആക്സസ് തരം തിരഞ്ഞെടുക്കുക.","farmer":"👨‍🌾 കർഷകൻ","admin":"🛡️ അഡ്മിൻ","mobile":"രജിസ്റ്റർ ചെയ്ത മൊബൈൽ നമ്പർ","mobile_ph":"10 അക്ക മൊബൈൽ നമ്പർ","token":"ഡിജിറ്റൽ ടോക്കൺ","token_ph":"ഉദാ. P101","farmer_login":"കർഷകനായി ലോഗിൻ ചെയ്യുക","new_farmer":"പുതിയ കർഷകനാണോ? ഇവിടെ രജിസ്റ്റർ ചെയ്യുക","farmer_note":"രജിസ്ട്രേഷനുശേഷം ലഭിച്ച മൊബൈൽ നമ്പറും ഡിജിറ്റൽ ടോക്കണും ഉപയോഗിച്ച് കർഷകർക്ക് ലോഗിൻ ചെയ്യാം.","username":"അഡ്മിൻ യൂസർനെയിം","username_ph":"അഡ്മിൻ യൂസർനെയിം","password":"പാസ്‌വേഡ്","password_ph":"അഡ്മിൻ പാസ്‌വേഡ്","admin_login":"അഡ്മിനായി ലോഗിൻ ചെയ്യുക","admin_note":"അഡ്മിൻ ആക്സസ് വാങ്ങൽ കേന്ദ്രത്തിലെ ജീവനക്കാർക്കും അഡ്മിനുകൾക്കുമാണ്.","language":"ഭാഷ","brand_desc":"സ്മാർട്ട് കാർഷിക വാങ്ങലും കർഷക സഹായ പ്ലാറ്റ്ഫോമും","slot":"📅 സ്മാർട്ട് സ്ലോട്ട് ബുക്കിംഗ്","queue":"🎟️ ഡിജിറ്റൽ ടോക്കൺ & ലൈവ് ക്യൂ","tracking":"📍 വാങ്ങൽ & ഷിപ്മെന്റ് ട്രാക്കിംഗ്","payment":"💳 സുതാര്യമായ പേയ്മെന്റ് നില","invalid_admin":"അഡ്മിൻ യൂസർനെയിം അല്ലെങ്കിൽ പാസ്‌വേഡ് തെറ്റാണ്.","invalid_farmer":"മൊബൈൽ നമ്പർ അല്ലെങ്കിൽ ഡിജിറ്റൽ ടോക്കൺ തെറ്റാണ്. പുതിയ കർഷകനാണെങ്കിൽ ആദ്യം രജിസ്റ്റർ ചെയ്യുക."},
    "or": {"title":"KisanGati କୁ ସ୍ୱାଗତ","sub":"ଜାରି ରଖିବା ପାଇଁ ଆପଣଙ୍କ ପ୍ରବେଶ ପ୍ରକାର ବାଛନ୍ତୁ।","farmer":"👨‍🌾 ଚାଷୀ","admin":"🛡️ ପ୍ରଶାସକ","mobile":"ପଞ୍ଜୀକୃତ ମୋବାଇଲ୍ ନମ୍ବର","mobile_ph":"୧୦ ଅଙ୍କର ମୋବାଇଲ୍ ନମ୍ବର","token":"ଡିଜିଟାଲ୍ ଟୋକେନ୍","token_ph":"ଯଥା P101","farmer_login":"ଚାଷୀ ଭାବେ ଲଗଇନ୍ କରନ୍ତୁ","new_farmer":"ନୂଆ ଚାଷୀ? ଏଠାରେ ପଞ୍ଜୀକରଣ କରନ୍ତୁ","farmer_note":"ପଞ୍ଜୀକରଣ ପରେ ମିଳିଥିବା ମୋବାଇଲ୍ ନମ୍ବର ଓ ଡିଜିଟାଲ୍ ଟୋକେନ୍‌ରେ ଚାଷୀ ଲଗଇନ୍ କରିପାରିବେ।","username":"ପ୍ରଶାସକ ୟୁଜରନେମ୍","username_ph":"ପ୍ରଶାସକ ୟୁଜରନେମ୍","password":"ପାସୱାର୍ଡ","password_ph":"ପ୍ରଶାସକ ପାସୱାର୍ଡ","admin_login":"ପ୍ରଶାସକ ଭାବେ ଲଗଇନ୍ କରନ୍ତୁ","admin_note":"ପ୍ରଶାସକ ପ୍ରବେଶ କ୍ରୟ କେନ୍ଦ୍ର କର୍ମଚାରୀ ଓ ପ୍ରଶାସକଙ୍କ ପାଇଁ।","language":"ଭାଷା","brand_desc":"ସ୍ମାର୍ଟ କୃଷି କ୍ରୟ ଏବଂ ଚାଷୀ ସହାୟତା ପ୍ଲାଟଫର୍ମ","slot":"📅 ସ୍ମାର୍ଟ ସ୍ଲଟ୍ ବୁକିଂ","queue":"🎟️ ଡିଜିଟାଲ୍ ଟୋକେନ୍ ଏବଂ ଲାଇଭ୍ ଧାଡ଼ି","tracking":"📍 କ୍ରୟ ଏବଂ ଶିପମେଣ୍ଟ ଟ୍ରାକିଂ","payment":"💳 ସ୍ୱଚ୍ଛ ପେମେଣ୍ଟ ସ୍ଥିତି","invalid_admin":"ପ୍ରଶାସକ ୟୁଜରନେମ୍ କିମ୍ବା ପାସୱାର୍ଡ ଭୁଲ।","invalid_farmer":"ମୋବାଇଲ୍ ନମ୍ବର କିମ୍ବା ଡିଜିଟାଲ୍ ଟୋକେନ୍ ଭୁଲ। ନୂଆ ଚାଷୀ ହେଲେ ପ୍ରଥମେ ପଞ୍ଜୀକରଣ କରନ୍ତୁ।"},
    "pa": {"title":"KisanGati ਵਿੱਚ ਜੀ ਆਇਆਂ ਨੂੰ","sub":"ਜਾਰੀ ਰੱਖਣ ਲਈ ਆਪਣੀ ਪਹੁੰਚ ਦੀ ਕਿਸਮ ਚੁਣੋ।","farmer":"👨‍🌾 ਕਿਸਾਨ","admin":"🛡️ ਐਡਮਿਨ","mobile":"ਰਜਿਸਟਰ ਕੀਤਾ ਮੋਬਾਈਲ ਨੰਬਰ","mobile_ph":"10 ਅੰਕਾਂ ਦਾ ਮੋਬਾਈਲ ਨੰਬਰ","token":"ਡਿਜ਼ਿਟਲ ਟੋਕਨ","token_ph":"ਜਿਵੇਂ P101","farmer_login":"ਕਿਸਾਨ ਵਜੋਂ ਲੌਗਇਨ ਕਰੋ","new_farmer":"ਨਵੇਂ ਕਿਸਾਨ ਹੋ? ਇੱਥੇ ਰਜਿਸਟਰ ਕਰੋ","farmer_note":"ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਤੋਂ ਬਾਅਦ ਮਿਲੇ ਮੋਬਾਈਲ ਨੰਬਰ ਅਤੇ ਡਿਜ਼ਿਟਲ ਟੋਕਨ ਨਾਲ ਕਿਸਾਨ ਲੌਗਇਨ ਕਰ ਸਕਦੇ ਹਨ।","username":"ਐਡਮਿਨ ਯੂਜ਼ਰਨੇਮ","username_ph":"ਐਡਮਿਨ ਯੂਜ਼ਰਨੇਮ","password":"ਪਾਸਵਰਡ","password_ph":"ਐਡਮਿਨ ਪਾਸਵਰਡ","admin_login":"ਐਡਮਿਨ ਵਜੋਂ ਲੌਗਇਨ ਕਰੋ","admin_note":"ਐਡਮਿਨ ਪਹੁੰਚ ਖਰੀਦ ਕੇਂਦਰ ਦੇ ਕਰਮਚਾਰੀਆਂ ਅਤੇ ਪ੍ਰਸ਼ਾਸਕਾਂ ਲਈ ਹੈ।","language":"ਭਾਸ਼ਾ","brand_desc":"ਸਮਾਰਟ ਖੇਤੀਬਾੜੀ ਖਰੀਦ ਅਤੇ ਕਿਸਾਨ ਸਹਾਇਤਾ ਪਲੇਟਫਾਰਮ","slot":"📅 ਸਮਾਰਟ ਸਲਾਟ ਬੁਕਿੰਗ","queue":"🎟️ ਡਿਜ਼ਿਟਲ ਟੋਕਨ ਅਤੇ ਲਾਈਵ ਕਤਾਰ","tracking":"📍 ਖਰੀਦ ਅਤੇ ਸ਼ਿਪਮੈਂਟ ਟ੍ਰੈਕਿੰਗ","payment":"💳 ਪਾਰਦਰਸ਼ੀ ਭੁਗਤਾਨ ਸਥਿਤੀ","invalid_admin":"ਐਡਮਿਨ ਯੂਜ਼ਰਨੇਮ ਜਾਂ ਪਾਸਵਰਡ ਗਲਤ ਹੈ।","invalid_farmer":"ਮੋਬਾਈਲ ਨੰਬਰ ਜਾਂ ਡਿਜ਼ਿਟਲ ਟੋਕਨ ਗਲਤ ਹੈ। ਨਵੇਂ ਕਿਸਾਨ ਹੋ ਤਾਂ ਪਹਿਲਾਂ ਰਜਿਸਟਰ ਕਰੋ।"}
}

LOGIN_HTML = r"""
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KisanGati — Login</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Inter,Arial,sans-serif;background:linear-gradient(135deg,#eef8f0,#f7fbf8);color:#183028;min-height:100vh;display:flex;align-items:center;justify-content:center}.wrap{width:min(1000px,94vw);display:grid;grid-template-columns:1.05fr .95fr;background:#fff;border-radius:24px;box-shadow:0 18px 55px rgba(0,80,45,.13);overflow:hidden}.brand{background:linear-gradient(145deg,#0b6b38,#149447);color:white;padding:58px 52px;display:flex;flex-direction:column;justify-content:center}.brand h1{font-size:44px;margin:0 0 14px}.brand p{font-size:18px;line-height:1.6;opacity:.93}.points{margin-top:26px;display:grid;gap:13px}.points div{padding:13px 15px;border:1px solid rgba(255,255,255,.25);border-radius:12px;background:rgba(255,255,255,.08)}.login{padding:42px;position:relative}.login h2{margin:0 0 7px;font-size:29px;color:#145d37}.sub{color:#64746c;margin-bottom:25px}.role-tabs{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}.role-tabs button{padding:13px;border:1px solid #d7e2db;border-radius:11px;background:#f7faf8;font-weight:800;color:#315343;cursor:pointer}.role-tabs button.active{background:#0f6d3b;color:#fff;border-color:#0f6d3b}.panel{display:none}.panel.active{display:block}.field{margin:14px 0}.field label{display:block;font-weight:700;margin-bottom:7px}.field input,.lang{width:100%;padding:13px 14px;border:1px solid #cfdad3;border-radius:10px;font-size:15px}.btn{width:100%;padding:13px;border:0;border-radius:10px;background:#0f6d3b;color:#fff;font-weight:800;font-size:15px;cursor:pointer}.secondary{background:#eaf5ee;color:#0f6d3b;margin-top:10px}.note{font-size:12px;color:#748078;margin-top:12px;line-height:1.5}.flash{padding:10px 12px;border-radius:9px;background:#fff3cd;color:#765b00;margin-bottom:15px}.language-box{margin-top:20px}.language-box label{font-weight:700;display:block;margin-bottom:7px}@media(max-width:760px){.wrap{grid-template-columns:1fr}.brand{padding:32px}.login{padding:28px}}
</style></head><body>
<div class="wrap"><div class="brand"><div style="font-size:50px">🌾</div><h1>KisanGati</h1><p id="brandDesc">Smart Agricultural Procurement & Farmer Assistance Platform</p><div class="points"><div id="pointSlot">📅 Smart slot booking</div><div id="pointQueue">🎟️ Digital token & live queue</div><div id="pointTracking">📍 Procurement & shipment tracking</div><div id="pointPayment">💳 Transparent payment status</div></div></div>
<div class="login"><h2 id="loginTitle">Welcome to KisanGati</h2><p class="sub" id="loginSub">Select your access type to continue.</p>
{% with messages=get_flashed_messages() %}{% if messages %}<div class="flash">{{messages[0]}}</div>{% endif %}{% endwith %}
<div class="role-tabs"><button id="farmerTab" class="active" onclick="showRole('farmer')">👨‍🌾 Farmer</button><button id="adminTab" onclick="showRole('admin')">🛡️ Admin</button></div>
<div id="farmerPanel" class="panel active"><form method="POST" action="/login"><input type="hidden" name="role" value="farmer"><input type="hidden" id="farmerLanguage" name="language" value="{{ language }}"><div class="field"><label id="mobileLabel">Registered Mobile Number</label><input name="mobile" inputmode="numeric" maxlength="10" required placeholder="10-digit mobile number" id="mobileInput"></div><div class="field"><label id="tokenLabel">Digital Token</label><input name="token" maxlength="4" required placeholder="e.g. P101" id="tokenInput"></div><button class="btn" id="farmerLoginBtn">Login as Farmer</button></form><a href="/new-farmer"><button class="btn secondary" type="button" id="newFarmerBtn">New Farmer? Register Here</button></a><div class="note" id="farmerNote">Farmers log in using the mobile number and digital token received after registration.</div></div>
<div id="adminPanel" class="panel"><form method="POST" action="/login"><input type="hidden" name="role" value="admin"><input type="hidden" id="adminLanguage" name="language" value="{{ language }}"><div class="field"><label id="usernameLabel">Admin Username</label><input name="username" required placeholder="Admin username" id="usernameInput"></div><div class="field"><label id="passwordLabel">Password</label><input name="password" type="password" required placeholder="Admin password" id="passwordInput"></div><button class="btn" id="adminLoginBtn">Login as Admin</button></form><div class="note" id="adminNote">Admin access is for procurement centre staff and administrators.</div></div>
<div class="language-box"><label id="languageLabel">Language</label><select class="lang" id="languageSelect" onchange="changeLoginLanguage(this.value)"><option value="en">English</option><option value="hi">हिन्दी</option><option value="bn">বাংলা</option><option value="ta">தமிழ்</option><option value="as">অসমীয়া</option><option value="te">తెలుగు</option><option value="mr">मराठी</option><option value="gu">ગુજરાતી</option><option value="kn">ಕನ್ನಡ</option><option value="ml">മലയാളം</option><option value="or">ଓଡ଼ିଆ</option><option value="pa">ਪੰਜਾਬੀ</option></select></div>
</div></div>
<script>
const loginTranslations={{ login_translations_json|safe }};
let currentLoginLanguage="{{ language }}";
function applyLoginLanguage(code){
  const t=loginTranslations[code]||loginTranslations.en; currentLoginLanguage=code;
  document.documentElement.lang=code;
  document.getElementById('loginTitle').textContent=t.title; document.getElementById('loginSub').textContent=t.sub;
  document.getElementById('farmerTab').textContent=t.farmer; document.getElementById('adminTab').textContent=t.admin;
  document.getElementById('mobileLabel').textContent=t.mobile; document.getElementById('mobileInput').placeholder=t.mobile_ph;
  document.getElementById('tokenLabel').textContent=t.token; document.getElementById('tokenInput').placeholder=t.token_ph;
  document.getElementById('farmerLoginBtn').textContent=t.farmer_login; document.getElementById('newFarmerBtn').textContent=t.new_farmer; document.getElementById('farmerNote').textContent=t.farmer_note;
  document.getElementById('usernameLabel').textContent=t.username; document.getElementById('usernameInput').placeholder=t.username_ph;
  document.getElementById('passwordLabel').textContent=t.password; document.getElementById('passwordInput').placeholder=t.password_ph;
  document.getElementById('adminLoginBtn').textContent=t.admin_login; document.getElementById('adminNote').textContent=t.admin_note;
  document.getElementById('languageLabel').textContent=t.language;
  document.getElementById('brandDesc').textContent=t.brand_desc; document.getElementById('pointSlot').textContent=t.slot; document.getElementById('pointQueue').textContent=t.queue; document.getElementById('pointTracking').textContent=t.tracking; document.getElementById('pointPayment').textContent=t.payment;
  document.getElementById('farmerLanguage').value=code; document.getElementById('adminLanguage').value=code; document.getElementById('languageSelect').value=code;
}
function changeLoginLanguage(code){ window.location.href='/?lang='+encodeURIComponent(code); }
function showRole(r){document.getElementById('farmerPanel').classList.toggle('active',r==='farmer');document.getElementById('adminPanel').classList.toggle('active',r==='admin');document.getElementById('farmerTab').classList.toggle('active',r==='farmer');document.getElementById('adminTab').classList.toggle('active',r==='admin');}
document.addEventListener('DOMContentLoaded',()=>applyLoginLanguage(currentLoginLanguage));
</script></body></html>
"""



def token_access_allowed(token):
    token = token.strip().upper()
    if session.get("role") == "admin":
        return True
    return session.get("role") == "farmer" and session.get("farmer_token") == token

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("role"):
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error":"Admin access required."}), 403
        return view(*args, **kwargs)
    return wrapped

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KisanGati | Smart Procurement</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,Helvetica,sans-serif;background:#f4f8f3;color:#1f2937}
header{background:#166534;color:white;padding:16px 6%;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}
.logo{font-size:23px;font-weight:800}.logo span{color:#bbf7d0}
nav a{color:white;text-decoration:none;margin-left:22px;font-weight:600;font-size:14px}
.hero{background:linear-gradient(135deg,#166534,#22c55e);color:white;padding:60px 6%;display:grid;grid-template-columns:1.4fr 1fr;gap:35px;align-items:center}
.hero h1{font-size:44px;line-height:1.08;margin-bottom:18px}.hero p{font-size:18px;line-height:1.6;max-width:650px}
.hero-card{background:white;color:#1f2937;border-radius:18px;padding:25px;box-shadow:0 15px 35px #064e3b55}
.hero-card h3{margin-bottom:15px}.queue-big{font-size:42px;color:#166534;font-weight:800}
.container{width:88%;max-width:1200px;margin:35px auto}
.section-title{margin-bottom:20px}.section-title h2{font-size:29px}.section-title p{color:#6b7280;margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.card{background:white;border-radius:16px;padding:22px;box-shadow:0 4px 16px #0000000d;border:1px solid #e5e7eb}
.card h3{margin-bottom:10px}.icon{font-size:30px;margin-bottom:12px}.muted{color:#6b7280;font-size:14px;line-height:1.5}
.dashboard{display:grid;grid-template-columns:1fr 1fr;gap:20px}
form{display:grid;gap:13px}label{font-size:14px;font-weight:700}
input,select{width:100%;padding:12px;border:1px solid #d1d5db;border-radius:9px;font-size:15px}
button,.btn{border:0;background:#166534;color:white;padding:12px 18px;border-radius:9px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block}
button:hover,.btn:hover{background:#14532d}.btn-light{background:#dcfce7;color:#166534}
.slot{display:flex;justify-content:space-between;align-items:center;padding:14px;border:1px solid #e5e7eb;border-radius:10px;margin:9px 0}
.available{color:#15803d;font-weight:700}.full{color:#dc2626;font-weight:700}
.token{font-size:38px;font-weight:800;color:#166534}
.progress{display:flex;justify-content:space-between;gap:5px;margin:20px 0;position:relative}
.step{flex:1;text-align:center;font-size:12px;color:#9ca3af}.step.done{color:#166534;font-weight:700}
.dot{width:26px;height:26px;border-radius:50%;background:#d1d5db;margin:0 auto 7px;line-height:26px;color:white}
.done .dot{background:#16a34a}
.alert{padding:12px 16px;border-radius:9px;background:#dcfce7;color:#166534;margin-bottom:18px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:12px;border-bottom:1px solid #e5e7eb;font-size:14px}
.badge{padding:5px 9px;border-radius:20px;background:#fef3c7;color:#92400e;font-size:12px;font-weight:700}
footer{background:#14532d;color:#d1fae5;padding:25px 6%;margin-top:50px;text-align:center}

.weather-card{background:linear-gradient(135deg,#eff6ff,#ffffff);border:1px solid #bfdbfe}
.weather-main{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
.weather-temp{font-size:46px;font-weight:800;color:#166534}
.weather-icon{font-size:48px}
.weather-meta{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px}
.weather-meta div{background:white;padding:10px;border-radius:9px;border:1px solid #e5e7eb}
.weather-warning{padding:12px 15px;border-radius:9px;margin-top:15px;font-weight:700}
.weather-warning.safe{background:#dcfce7;color:#166534}
.weather-warning.warn{background:#fef3c7;color:#92400e}
.weather-warning.danger{background:#fee2e2;color:#991b1b}
.weather-loading{color:#6b7280}
@media(max-width:550px){.weather-meta{grid-template-columns:1fr 1fr}}

/* Bank details + live shipment tracking */
.form-section-title{font-size:18px;color:#166534;margin:20px 0 5px;padding-top:12px;border-top:1px solid #e5e7eb}
.form-help{font-size:12px;color:#6b7280;margin-bottom:5px}
.tracking-card{background:linear-gradient(135deg,#f0fdf4,#ffffff);border:1px solid #bbf7d0}
.tracking-search{display:grid;grid-template-columns:1fr auto;gap:10px;margin-bottom:16px}
.tracking-status{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.track-pill{background:white;border:1px solid #e5e7eb;border-radius:10px;padding:12px}
.track-pill small{display:block;color:#6b7280;margin-bottom:4px}
.track-stage{font-size:22px;font-weight:800;color:#166534}
.tracking-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:15px}
#trackingMap{height:330px;border-radius:14px;margin-top:16px;border:1px solid #d1d5db;overflow:hidden}
.stage-row{display:flex;gap:5px;flex-wrap:wrap;margin-top:15px}
.stage-chip{padding:7px 10px;border-radius:20px;background:#dcfce7;color:#166534;font-size:12px;font-weight:700}
.stage-chip.active{background:#166534;color:white}
.gps-live{display:inline-flex;align-items:center;gap:6px;font-weight:700;color:#166534}
.feature-token-bar{display:grid;grid-template-columns:1fr auto;gap:10px;margin-bottom:18px}
.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.smart-feature-card{min-height:340px}
.smart-feature-card h3{color:#166534;margin-bottom:9px}
.effort-score{display:flex;align-items:baseline;gap:7px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:13px 15px;margin:14px 0;font-size:14px}
.effort-score b{font-size:32px;color:#166534;margin-left:auto}
.effort-score small{color:#6b7280}
.effort-metrics{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:12px}
.effort-metrics div{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:10px}
.effort-metrics b{display:block;font-size:20px;color:#166534;margin-bottom:3px}
.effort-metrics span{font-size:11px;color:#6b7280}
.lot-trace-timeline{margin:14px 0;display:grid;gap:8px}
.trace-item{display:grid;grid-template-columns:26px 1fr auto;gap:8px;align-items:center;padding:9px;border:1px solid #e5e7eb;border-radius:10px;background:#fff}
.trace-dot{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#e5e7eb;color:#6b7280;font-size:11px;font-weight:800}
.trace-dot.done{background:#166534;color:#fff}.trace-dot.rejected{background:#b91c1c;color:#fff}
.trace-name{font-weight:700;font-size:12px}.trace-detail{font-size:10px;color:#6b7280;margin-top:2px}
.trace-status{font-size:10px;font-weight:800;padding:4px 7px;border-radius:12px;background:#fef3c7;color:#92400e}.trace-status.done{background:#dcfce7;color:#166534}.trace-status.rejected{background:#fee2e2;color:#991b1b}
.trace-controls{display:grid;gap:8px;margin-top:12px}.trace-controls select,.trace-controls input,.rejection-card select,.rejection-card textarea{width:100%}
.rejection-history{margin-top:12px;display:grid;gap:8px;max-height:150px;overflow:auto}.rejection-item{padding:9px;border-radius:9px;background:#fff7f7;border:1px solid #fecaca}.rejection-item b{font-size:12px;color:#991b1b}.rejection-item p{font-size:11px;color:#4b5563;margin-top:4px}
@media(max-width:950px){.feature-grid{grid-template-columns:1fr}.smart-feature-card{min-height:0}}
@media(max-width:700px){.feature-token-bar{grid-template-columns:1fr}}

@media(max-width:700px){.tracking-status{grid-template-columns:1fr}.tracking-search{grid-template-columns:1fr}}


@media(max-width:800px){.hero,.dashboard{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}.hero h1{font-size:35px}}
@media(max-width:550px){
  .grid{grid-template-columns:1fr}
  nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  nav a{margin-left:8px}
  #languageSelect{margin-left:8px!important;display:inline-block!important}
  .container{width:92%}
}

.ai-fab{position:fixed;right:24px;bottom:24px;width:62px;height:62px;border-radius:50%;background:#166534;color:white;border:3px solid white;box-shadow:0 8px 25px #0003;z-index:100;display:flex;align-items:center;justify-content:center;font-size:27px;cursor:pointer}
.ai-panel{position:fixed;right:24px;bottom:98px;width:370px;max-width:calc(100vw - 30px);background:white;border-radius:18px;box-shadow:0 12px 40px #0004;border:1px solid #d1d5db;z-index:99;overflow:hidden;display:none}
.ai-head{background:#166534;color:white;padding:15px 18px;display:flex;justify-content:space-between;align-items:center}
.ai-head button{background:transparent;padding:0;font-size:20px}
.ai-body{padding:15px;height:390px;overflow-y:auto}
.ai-msg{padding:10px 12px;border-radius:12px;margin:8px 0;max-width:88%;line-height:1.45;white-space:pre-wrap}
.ai-user{background:#dcfce7;margin-left:auto}
.ai-bot{background:#f3f4f6;margin-right:auto}
.ai-input{display:flex;gap:7px;padding:12px;border-top:1px solid #e5e7eb}
.ai-input input{flex:1}
.ai-mic{min-width:45px!important;padding:10px!important}
.ai-mic.listening{background:#dc2626}
.ai-status{font-size:12px;color:#6b7280;padding:0 15px 8px}
@media(max-width:550px){.ai-panel{right:10px;bottom:90px}.ai-fab{right:15px;bottom:15px}}

</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
</head>
<body>
<header>
  <div class="logo">🌾 Kisan<span>Gati</span></div>
  <nav>
    <a href="{{ url_for('farmer_page') if role == 'farmer' else url_for('admin_page') }}" data-i18n="home"></a>
    {% if role == 'farmer' %}<a href="#register" data-i18n="register_nav"></a><a href="#queue" data-i18n="queue_nav"></a><a href="#status" data-i18n="status_nav"></a><a href="#tracking">Tracking</a><a href="#weather" data-i18n="weather_title" style="margin-left:22px"></a>{% else %}<a href="#queue" data-i18n="queue_nav"></a><a href="#status" data-i18n="status_nav"></a><a href="#tracking">Tracking</a><a href="#smartFeatures">Admin Features</a>{% endif %}
    <select id="languageSelect" onchange="changeLanguage(this.value)" aria-label="Select language" style="margin-left:18px;padding:8px 10px;border-radius:8px;border:2px solid #bbf7d0;background:white;color:#166534;font-weight:700;min-width:130px;display:inline-block;">
      {% for code, lang in languages.items() %}<option value="{{code}}" {% if code == language %}selected{% endif %}>{{lang["name"]}}</option>{% endfor %}
    </select>
    <a href="{{ url_for('logout') }}" style="margin-left:12px">Logout</a>
  </nav>
</header>

{% with messages=get_flashed_messages() %}
{% if messages %}<div class="container"><div class="alert">{{messages[0]}}</div></div>{% endif %}
{% endwith %}

{% if role == "farmer" %}
<section class="hero">
  <div>
    <h1 data-i18n="hero_title"></h1>
    <p data-i18n="hero_desc"></p>
    <br><a class="btn" href="#register" data-i18n="book"></a>
  </div>
  <div class="hero-card">
    <h3 data-i18n="centre"></h3>
    <p class="muted" data-i18n="current_token"></p>
    <div class="queue-big">P097</div>
    <p class="muted" data-i18n="waiting"></p>
    <hr style="margin:15px 0;border:0;border-top:1px solid #eee">
    <p><b data-i18n="centre_status"></b> <span class="available" data-i18n="open"></span></p>
  </div>
</section>

<div class="container">
<div id="adminConsole" style="display:{% if role == "admin" %}block{% else %}none{% endif %};margin-bottom:30px"><div class="section-title"><h2>🛡️ Admin Procurement Console</h2><p>Manage queue, procurement lots, quality decisions, GPS updates and payment workflow.</p></div><div class="dashboard"><div class="card"><p class="muted">Registered Farmers</p><h2 id="adminFarmerCount">--</h2></div><div class="card"><p class="muted">Current Queue Token</p><h2 id="adminQueueToken">--</h2></div><div class="card"><p class="muted">Tracked Lots</p><h2 id="adminTrackedLots">--</h2></div><div class="card"><p class="muted">Rejections Recorded</p><h2 id="adminRejections">--</h2></div></div></div>
<section>
<div class="section-title"><h2 data-i18n="how_title"></h2><p data-i18n="how_desc"></p></div>
<div class="grid">
  <div class="card"><div class="icon">🧑‍🌾</div><h3 data-i18n="reg"></h3><p class="muted" data-i18n="reg_desc"></p></div>
  <div class="card"><div class="icon">📅</div><h3 data-i18n="slot"></h3><p class="muted" data-i18n="slot_desc"></p></div>
  <div class="card"><div class="icon">🎟️</div><h3 data-i18n="token"></h3><p class="muted" data-i18n="token_desc"></p></div>
  <div class="card"><div class="icon">🔔</div><h3 data-i18n="notify"></h3><p class="muted" data-i18n="notify_desc"></p></div>
  <div class="card"><div class="icon">📦</div><h3 data-i18n="proc"></h3><p class="muted" data-i18n="proc_desc"></p></div>
  <div class="card"><div class="icon">💳</div><h3 data-i18n="pay"></h3><p class="muted" data-i18n="pay_desc"></p></div>
</div>
</section>

<section id="weather" style="margin-top:55px">
<div class="section-title">
  <h2 data-i18n="weather_title"></h2>
  <p data-i18n="weather_sub"></p>
</div>
<div class="card weather-card">
  <div id="weatherLoading" class="weather-loading" data-i18n="weather_getting"></div>
  <div id="weatherBox" style="display:none">
    <div class="weather-main">
      <div>
        <div id="weatherLocation" style="font-weight:800;font-size:20px"></div>
        <div id="weatherCondition" class="muted" style="margin-top:5px"></div>
      </div>
      <div>
        <span id="weatherIcon" class="weather-icon">🌤️</span>
        <span id="weatherTemp" class="weather-temp"></span>
      </div>
    </div>
    <div class="weather-meta">
      <div><b data-i18n="weather_humidity"></b><br><span id="weatherHumidity">--</span></div>
      <div><b data-i18n="weather_wind"></b><br><span id="weatherWind">--</span></div>
      <div><b data-i18n="weather_rain"></b><br><span id="weatherRain">--</span></div>
    </div>
    <div id="weatherWarning" class="weather-warning safe"></div>
    <button type="button" onclick="loadWeather()" style="margin-top:12px" data-i18n="weather_refresh"></button>
  </div>
  <div id="weatherError" style="display:none" class="weather-warning warn"></div>
</div>
</section>

<section id="register" style="margin-top:55px">
<div class="section-title"><h2 data-i18n="reg_title"></h2><p data-i18n="reg_sub"></p></div>
<div class="dashboard">
<div class="card">
<form method="POST" action="/register"><input type="hidden" name="language" id="formLanguage" value="{{language}}">
<label data-i18n="farmer_name"></label><input name="name" placeholder="e.g. Ramesh Das" required>
<label data-i18n="mobile"></label><input name="mobile" placeholder="10-digit mobile number" required>
<label data-i18n="farmer_id"></label><input name="farmer_id" placeholder="e.g. F10234" required>
<label data-i18n="crop"></label><select name="crop"><option>Paddy</option><option>Wheat</option><option>Maize</option><option>Other</option></select>
<label data-i18n="quantity"></label><input type="number" name="quantity" min="1" placeholder="40" required>

<div class="form-section-title" data-i18n="bank_title"></div>
<p class="form-help" data-i18n="bank_help"></p>
<label data-i18n="bank_name"></label><input name="bank_name" data-i18n-placeholder="bank_name_ph" placeholder="e.g. State Bank of India" required>
<label data-i18n="account_holder"></label><input name="account_holder" data-i18n-placeholder="account_holder_ph" placeholder="As per bank account" required>
<label data-i18n="account_number"></label><input name="account_number" data-i18n-placeholder="account_number_ph" inputmode="numeric" pattern="[0-9]{9,18}" maxlength="18" placeholder="9–18 digit account number" required>
<label data-i18n="ifsc"></label><input name="ifsc_code" data-i18n-placeholder="ifsc_ph" maxlength="11" pattern="[A-Za-z]{4}0[A-Za-z0-9]{6}" placeholder="e.g. SBIN0001234" style="text-transform:uppercase" required>

<label data-i18n="available_slot"></label>
<select name="slot">
  <option>10:00 AM - 11:00 AM</option>
  <option>11:00 AM - 12:00 PM</option>
  <option>01:00 PM - 02:00 PM</option>
  <option>02:00 PM - 03:00 PM</option>
</select>
<button type="submit" data-i18n="submit"></button>
</form>
</div>
<div class="card">
<h3 data-i18n="today_slots"></h3>
{% for s in slots %}
<div class="slot"><span>{{s[0]}}</span><span class="{{'full' if s[1]>=10 else 'available'}}" data-slot-count="{{s[1]}}"></span></div>
{% endfor %}
<p class="muted" style="margin-top:15px" data-i18n="slots_help"></p>
</div>
</div>
</section>

{% endif %}

<section id="queue" style="margin-top:55px">
<div class="section-title"><h2 data-i18n="live"></h2><p data-i18n="live_sub"></p></div>
<div class="card">
<div class="dashboard">
<div>
<p class="muted" data-i18n="serving"></p><div class="token">P097</div>
<p><b data-i18n="next"></b> P098 → P099 → P100 → P101</p>
</div>
<div>
<p class="muted" data-i18n="sample"></p><div class="token">P104</div>
<p><b data-i18n="away"></b></p>
{% if role == "admin" %}<button onclick="simulateQueue()" style="margin-top:10px" data-i18n="simulate"></button>{% endif %}
</div>
</div>
</div>
</section>

<section id="status" style="margin-top:55px">
<div class="section-title"><h2 data-i18n="status_title"></h2><p data-i18n="status_sub"></p></div>
<div class="card">
<div class="progress">
{% for x in [('booking','Booking'),('arrived','Arrived'),('queue','Queue'),('quality','Quality Check'),('weighing','Weighing'),('procurement','Procurement'),('payment_processing','Payment Processing'),('payment_received','Payment Received')] %}
<div class="step {{'done' if loop.index <= 6 else ''}}"><div class="dot">{{'✓' if loop.index <= 6 else loop.index}}</div>{{trans[x[0]]}}</div>
{% endfor %}
</div>
<hr style="border:0;border-top:1px solid #eee;margin:15px 0">
<div class="dashboard">
<div><p class="muted">Procurement</p><h3>Completed ✓</h3><p>Quantity: <b>40 quintals</b></p></div>
<div><p class="muted">Payment</p><h3>₹52,000</h3><p><span class="badge">Processing</span></p></div>
</div>
</div>
</section>

<section id="tracking" style="margin-top:55px">
<div class="section-title"><h2 data-i18n="tracking_title"></h2><p data-i18n="tracking_sub"></p></div>
<div class="card tracking-card">
  <div class="tracking-search">
    <input id="trackingToken" data-i18n-placeholder="tracking_token_ph" placeholder="Enter token e.g. P101" maxlength="4">
    <button type="button" onclick="loadTracking()" data-i18n="track_lot"></button>
  </div>
  <div id="trackingEmpty" class="muted" data-i18n="tracking_empty"></div>
  <div id="trackingContent" style="display:none">
    <div class="tracking-status">
      <div class="track-pill"><small data-i18n="tracking_id"></small><b id="trackingId">--</b></div>
      <div class="track-pill"><small data-i18n="current_stage"></small><div id="trackingStage" class="track-stage">--</div></div>
      <div class="track-pill"><small data-i18n="current_location"></small><b id="trackingLocation">--</b></div>
      <div class="track-pill"><small data-i18n="last_gps"></small><b id="trackingUpdated">--</b></div>
    </div>
    <div class="stage-row" id="trackingStages"></div>
    {% if role == "admin" %}<div class="tracking-actions">
      <button type="button" onclick="startGPSTracking()" data-i18n="start_gps"></button>
      <button type="button" class="btn-light" onclick="stopGPSTracking()" data-i18n="stop_gps"></button>
      <button type="button" class="btn-light" onclick="simulateTrackingStage()" data-i18n="simulate_stage"></button>
    </div>{% else %}<p class="form-help" style="margin-top:12px">Farmer view is read-only. Location and processing updates are managed by the procurement centre.</p>{% endif %}
    <div id="gpsStatus" class="form-help" style="margin-top:10px"></div>
    <div id="trackingMap"></div>
    {% if role == "farmer" %}
    <div class="card" style="margin-top:16px"><h3>🔗 My Lot Trace</h3><p class="muted">Farmer → Quality Check → Procurement → Payment</p><div id="farmerLotTraceTimeline" class="lot-trace-timeline"></div><h3 style="margin-top:18px">📝 Quality Rejection Updates</h3><div id="farmerRejectionHistory" class="rejection-history"></div></div>
    {% endif %}
  </div>
</div>
</section>

{% if role == "admin" %}
<section id="smartFeatures" style="margin-top:55px">
<div class="section-title"><h2 data-i18n="effort_title"></h2><p data-i18n="effort_desc"></p></div>
<div class="feature-token-bar">
  <input id="featureToken" data-i18n-placeholder="tracking_token_ph" placeholder="Enter token e.g. P101" maxlength="4">
  <button type="button" onclick="loadSmartFeatures()" data-i18n="track_lot"></button>
</div>
<div class="feature-grid">
  <div class="card smart-feature-card effort-card">
    <h3 data-i18n="effort_title"></h3>
    <p class="muted" data-i18n="effort_desc"></p>
    <div id="effortNoData" class="form-help" data-i18n="effort_no_data"></div>
    <div id="effortContent" style="display:none">
      <div class="effort-score"><span data-i18n="effort_score"></span><b id="effortScore">--</b><small>/100</small></div>
      <div class="effort-metrics">
        <div><b id="effortVisits">0</b><span data-i18n="effort_visits"></span></div>
        <div><b id="effortUnnecessary">0</b><span data-i18n="effort_unnecessary"></span></div>
        <div><b id="effortWait">0</b><span data-i18n="effort_wait"></span></div>
        <div><b id="effortRepeat">0</b><span data-i18n="effort_repeat"></span></div>
      </div>
      <p class="form-help" data-i18n="effort_score_help"></p>
      <button type="button" onclick="recordFarmerVisit()" data-i18n="effort_record_visit"></button>
    </div>
  </div>

  <div class="card smart-feature-card trace-card">
    <h3 data-i18n="lot_title"></h3>
    <p class="muted" data-i18n="lot_desc"></p>
    <div id="lotTraceEmpty" class="form-help" data-i18n="effort_no_data"></div>
    <div id="lotTraceContent" style="display:none">
      <div id="lotTraceTimeline" class="lot-trace-timeline"></div>
      <div class="trace-controls">
        <select id="lotTraceStep">
          <option value="quality" data-i18n="lot_quality"></option>
          <option value="procurement" data-i18n="lot_procurement"></option>
          <option value="payment" data-i18n="lot_payment"></option>
        </select>
        <select id="lotTraceStatus">
          <option value="Completed" data-i18n="lot_completed"></option>
          <option value="Pending" data-i18n="lot_pending"></option>
          <option value="Rejected" data-i18n="lot_rejected"></option>
        </select>
        <input id="lotTraceDetail" data-i18n-placeholder="lot_step_help" placeholder="Step detail">
        <button type="button" onclick="updateLotTrace()" data-i18n="lot_update"></button>
      </div>
      <p class="form-help" data-i18n="lot_step_help"></p>
    </div>
  </div>

  <div class="card smart-feature-card rejection-card">
    <h3 data-i18n="rejection_title"></h3>
    <p class="muted" data-i18n="rejection_desc"></p>
    <div id="rejectionNoData" class="form-help" data-i18n="rejection_none"></div>
    <div id="rejectionContent">
      <select id="rejectionReason">
        <option value="" data-i18n="rejection_select"></option>
        <option data-i18n="rejection_quality"></option>
        <option data-i18n="rejection_moisture"></option>
        <option data-i18n="rejection_impurity"></option>
        <option data-i18n="rejection_damage"></option>
        <option data-i18n="rejection_quantity"></option>
        <option data-i18n="rejection_other"></option>
      </select>
      <textarea id="rejectionGuidance" data-i18n-placeholder="rejection_guidance" placeholder="Actionable guidance" rows="3"></textarea>
      <button type="button" onclick="saveRejection()" data-i18n="rejection_save"></button>
      <div id="rejectionHistory" class="rejection-history"></div>
    </div>
  </div>
</div>
</section>
{% endif %}

{% if role == "admin" %}
<section style="margin-top:55px">
<div class="section-title"><h2 data-i18n="recent"></h2><p data-i18n="recent_sub"></p></div>
<div class="card" style="overflow:auto">
<table><tr><th>Token</th><th data-i18n="farmer_name"></th><th data-i18n="crop"></th><th data-i18n="quantity"></th><th data-i18n="available_slot"></th><th data-i18n="status"></th></tr>
{% for f in farmers %}
<tr><td><b>{{f[0]}}</b></td><td>{{f[1]}}</td><td>{{f[2]}}</td><td>{{f[3]}} qtl</td><td>{{f[4]}}</td><td><span class="badge">{{f[5]}}</span></td></tr>
{% else %}<tr><td colspan="6">No registrations yet.</td></tr>{% endfor %}
</table>
</div>
</section>
</div>

{% endif %}
<footer data-i18n="footer"></footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const translations = {{ translations_json|safe }};
let currentLanguage = "{{language}}";
let latestWeather = null;

function getSavedUserToken(){
  return localStorage.getItem("kisanGatiUserToken") || "{{ session.get('farmer_token','') }}" || "";
}

function saveDetectedToken(){
  const alertBox = document.querySelector(".alert");
  if(!alertBox) return;
  const match = alertBox.textContent.match(/\bP\d{3}\b/i);
  if(match) localStorage.setItem("kisanGatiUserToken", match[0].toUpperCase());
}

function applyLanguage(lang){
  currentLanguage = translations[lang] ? lang : "en";
  const t = translations[currentLanguage];
  document.documentElement.lang = currentLanguage;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (t[key] !== undefined) el.innerHTML = t[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (t[key] !== undefined) el.placeholder = t[key];
  });
  document.querySelectorAll("[data-slot-count]").forEach(el => {
    const count = parseInt(el.dataset.slotCount, 10);
    el.textContent = count >= 10 ? t.full : t.slots_left.replace("{n}", 10-count);
  });
  const formLang = document.getElementById("formLanguage");
  if(formLang) formLang.value = currentLanguage;
  const selector = document.getElementById("languageSelect");
  if(selector) selector.value = currentLanguage;
  localStorage.setItem("kisanGatiLanguage", currentLanguage);
}
function changeLanguage(lang){ applyLanguage(lang); }

async function loadWeather(){
  const loading = document.getElementById("weatherLoading");
  const box = document.getElementById("weatherBox");
  const error = document.getElementById("weatherError");
  const warning = document.getElementById("weatherWarning");
  loading.style.display = "block";
  box.style.display = "none";
  error.style.display = "none";

  if(!navigator.geolocation){
    loading.style.display = "none";
    error.style.display = "block";
    error.textContent = (translations[currentLanguage] || translations.en).weather_error;
    return;
  }

  navigator.geolocation.getCurrentPosition(async position => {
    try{
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m&hourly=precipitation_probability,weather_code&timezone=auto&forecast_days=1`;
      const response = await fetch(url);
      if(!response.ok) throw new Error("Weather API error");
      const data = await response.json();

      const code = data.current.weather_code;
      const condition = weatherDescription(code);
      const icon = weatherIcon(code);
      const rainChance = nearestRainChance(data);
      const temp = Math.round(data.current.temperature_2m);
      const humidity = Math.round(data.current.relative_humidity_2m);
      const wind = Math.round(data.current.wind_speed_10m);

      latestWeather = {
        location: `${lat.toFixed(2)}, ${lon.toFixed(2)}`,
        condition: condition,
        temperature: temp,
        humidity: humidity,
        wind: wind,
        rain_chance: rainChance,
        code: code
      };

      document.getElementById("weatherLocation").textContent =
        `📍 ${lat.toFixed(2)}, ${lon.toFixed(2)}`;
      document.getElementById("weatherCondition").textContent = `${icon} ${condition}`;
      document.getElementById("weatherIcon").textContent = icon;
      document.getElementById("weatherTemp").textContent = `${temp}°C`;
      document.getElementById("weatherHumidity").textContent = `${humidity}%`;
      document.getElementById("weatherWind").textContent = `${wind} km/h`;
      document.getElementById("weatherRain").textContent = `${rainChance}%`;

      const t = translations[currentLanguage] || translations.en;
      let warningText = t.weather_safe;
      let warningClass = "safe";

      if([95,96,99].includes(code)){
        warningText = t.weather_storm_warn;
        warningClass = "danger";
      } else if(rainChance >= 70 || data.current.rain > 0 || data.current.precipitation > 0){
        warningText = t.weather_rain_warn;
        warningClass = "warn";
      } else if(temp >= 38){
        warningText = t.weather_heat_warn;
        warningClass = "warn";
      } else if(wind >= 40){
        warningText = t.weather_wind_warn;
        warningClass = "warn";
      }

      warning.textContent = warningText;
      warning.className = `weather-warning ${warningClass}`;
      loading.style.display = "none";
      box.style.display = "block";
    }catch(e){
      loading.style.display = "none";
      error.style.display = "block";
      error.textContent = (translations[currentLanguage] || translations.en).weather_error;
    }
  }, () => {
    loading.style.display = "none";
    error.style.display = "block";
    error.textContent = (translations[currentLanguage] || translations.en).weather_enable;
  }, {enableHighAccuracy:false, timeout:10000, maximumAge:600000});
}

function nearestRainChance(data){
  const now = new Date();
  const times = data.hourly.time || [];
  const probs = data.hourly.precipitation_probability || [];
  if(!times.length) return 0;
  let best = 0, bestDiff = Infinity;
  for(let i=0;i<times.length;i++){
    const diff = Math.abs(new Date(times[i]).getTime() - now.getTime());
    if(diff < bestDiff){ bestDiff = diff; best = probs[i] || 0; }
  }
  return Math.round(best);
}

function weatherDescription(code){
  const map = {
    0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
    45:"Fog",48:"Rime fog",51:"Light drizzle",53:"Drizzle",55:"Heavy drizzle",
    56:"Freezing drizzle",57:"Heavy freezing drizzle",61:"Light rain",63:"Rain",
    65:"Heavy rain",66:"Freezing rain",67:"Heavy freezing rain",
    71:"Light snow",73:"Snow",75:"Heavy snow",77:"Snow grains",
    80:"Rain showers",81:"Rain showers",82:"Heavy rain showers",
    85:"Snow showers",86:"Heavy snow showers",95:"Thunderstorm",
    96:"Thunderstorm with hail",99:"Thunderstorm with heavy hail"
  };
  return map[code] || "Changing weather";
}

function weatherIcon(code){
  if([95,96,99].includes(code)) return "⛈️";
  if([61,63,65,80,81,82].includes(code)) return "🌧️";
  if([51,53,55,56,57].includes(code)) return "🌦️";
  if([45,48].includes(code)) return "🌫️";
  if([71,73,75,77,85,86].includes(code)) return "❄️";
  if([1,2,3].includes(code)) return "⛅";
  return "☀️";
}


let trackingToken = "";
let gpsWatchId = null;
let trackingMap = null;
let trackingMarker = null;
let trackingRefreshTimer = null;
const TRACKING_STAGES = ["At Procurement Centre","Quality Check","Weighing","Processing","Shipped","In Transit","Delivered"];

function normalizeTrackingToken(value){
  const m=(value||"").toUpperCase().match(/P\s*(\d{3})/);
  return m ? `P${m[1]}` : "";
}

function initTrackingMap(){
  if(trackingMap || typeof L === "undefined") return;
  trackingMap=L.map("trackingMap").setView([20.5937,78.9629],5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
    maxZoom:19, attribution:"© OpenStreetMap contributors"
  }).addTo(trackingMap);
}

function updateTrackingMap(lat,lon,accuracy){
  if(lat==null || lon==null) return;
  initTrackingMap();
  if(!trackingMap) return;
  const point=[Number(lat),Number(lon)];
  trackingMap.setView(point,16);
  if(trackingMarker) trackingMarker.setLatLng(point);
  else trackingMarker=L.marker(point).addTo(trackingMap).bindPopup((translations[currentLanguage] || translations.en).loc_live).openPopup();
  if(accuracy) trackingMarker.bindTooltip((translations[currentLanguage] || translations.en).gps_live.replace("{accuracy}",Math.round(accuracy)).replace(" • Last update {time}",""));
}

function trackingStageText(stage){
  const t=translations[currentLanguage] || translations.en;
  const map={
    "At Procurement Centre":"stage_centre",
    "Quality Check":"stage_quality",
    "Weighing":"stage_weighing",
    "Processing":"stage_processing",
    "Shipped":"stage_shipped",
    "In Transit":"stage_transit",
    "Delivered":"stage_delivered"
  };
  return t[map[stage]] || stage;
}
function trackingLocationText(location){
  const t=translations[currentLanguage] || translations.en;
  const map={
    "Procurement Centre":"loc_centre",
    "Quality Check Unit":"loc_quality",
    "Weighing Bay":"loc_weighing",
    "Processing Unit":"loc_processing",
    "Dispatch Centre":"loc_dispatch",
    "Live GPS Location":"loc_live",
    "Destination Centre":"loc_destination"
  };
  return t[map[location]] || location;
}
function renderTrackingStages(active){
  const box=document.getElementById("trackingStages");
  box.innerHTML="";
  TRACKING_STAGES.forEach(stage=>{
    const chip=document.createElement("span"); chip.className="stage-chip"+(stage===active?" active":"");
    chip.textContent=trackingStageText(stage); box.appendChild(chip);
  });
}

function formatTrackingTime(value){
  if(!value) return "Not available";
  try{return new Date(value).toLocaleString();}catch(e){return value;}
}

async function loadTracking(tokenOverride=null){
  const input=document.getElementById("trackingToken");
  const token=normalizeTrackingToken(tokenOverride || input.value);
  if(!token){ alert((translations[currentLanguage] || translations.en).valid_token); return; }
  trackingToken=token; input.value=token;
  try{
    const response=await fetch(`/api/tracking/${token}`);
    const d=await response.json();
    if(!response.ok) throw new Error(d.error || (translations[currentLanguage] || translations.en).tracking_not_found);
    document.getElementById("trackingEmpty").style.display="none";
    document.getElementById("trackingContent").style.display="block";
    document.getElementById("trackingId").textContent=d.tracking_id;
    document.getElementById("trackingStage").textContent=trackingStageText(d.stage);
    document.getElementById("trackingLocation").textContent=trackingLocationText(d.location);
    document.getElementById("trackingUpdated").textContent=formatTrackingTime(d.last_updated);
    renderTrackingStages(d.stage);
    const t=translations[currentLanguage] || translations.en; const gpsText=d.gps_active ? t.gps_active : t.gps_stopped;
    document.getElementById("gpsStatus").textContent=gpsText;
    updateTrackingMap(d.latitude,d.longitude,d.accuracy);
    if(document.getElementById("farmerLotTraceTimeline")){ loadFarmerTraceAndRejections(token); }
    if(document.getElementById("adminConsole")){ loadAdminSummary(); }
    if(!trackingRefreshTimer) trackingRefreshTimer=setInterval(()=>{ if(trackingToken) loadTracking(trackingToken); },5000);
  }catch(e){
    alert(e.message || (translations[currentLanguage] || translations.en).tracking_load_error);
  }
}

function startGPSTracking(){
  if(!trackingToken){ alert((translations[currentLanguage] || translations.en).load_token_first); return; }
  if(!navigator.geolocation){ alert((translations[currentLanguage] || translations.en).gps_unsupported); return; }
  if(gpsWatchId!==null) return;
  document.getElementById("gpsStatus").textContent=(translations[currentLanguage] || translations.en).gps_permission;
  gpsWatchId=navigator.geolocation.watchPosition(async position=>{
    const {latitude,longitude,accuracy}=position.coords;
    try{
      const response=await fetch(`/api/tracking/${trackingToken}/location`,{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({latitude,longitude,accuracy})
      });
      const d=await response.json();
      if(!response.ok) throw new Error(d.error || (translations[currentLanguage] || translations.en).gps_update_error.replace("{message}","GPS update failed"));
      document.getElementById("gpsStatus").textContent=(translations[currentLanguage] || translations.en).gps_live.replace("{accuracy}",Math.round(accuracy||0)).replace("{time}",new Date().toLocaleTimeString());
      updateTrackingMap(latitude,longitude,accuracy);
      document.getElementById("trackingStage").textContent=trackingStageText("In Transit");
      renderTrackingStages("In Transit");
      document.getElementById("trackingLocation").textContent=trackingLocationText("Live GPS Location");
      document.getElementById("trackingUpdated").textContent=new Date().toLocaleString();
    }catch(e){document.getElementById("gpsStatus").textContent=(translations[currentLanguage] || translations.en).gps_update_error.replace("{message}",e.message);}
  },error=>{
    document.getElementById("gpsStatus").textContent=(translations[currentLanguage] || translations.en).gps_error.replace("{message}",error.message);
    stopGPSTracking(false);
  },{enableHighAccuracy:true,maximumAge:3000,timeout:15000});
}

async function stopGPSTracking(showMessage=true){
  if(gpsWatchId!==null){navigator.geolocation.clearWatch(gpsWatchId); gpsWatchId=null;}
  if(trackingToken){
    try{await fetch(`/api/tracking/${trackingToken}/stop`,{method:"POST"});}catch(e){}
  }
  if(showMessage) document.getElementById("gpsStatus").textContent=(translations[currentLanguage] || translations.en).gps_stopped;
}

async function simulateTrackingStage(){
  if(!trackingToken){ alert((translations[currentLanguage] || translations.en).load_token_first); return; }
  try{
    const current=(await (await fetch(`/api/tracking/${trackingToken}`)).json()).stage;
    const idx=TRACKING_STAGES.indexOf(current);
    const next=TRACKING_STAGES[Math.min(idx+1,TRACKING_STAGES.length-1)];
    if(next===current){alert((translations[currentLanguage] || translations.en).lot_delivered);return;}
    const response=await fetch(`/api/tracking/${trackingToken}/stage`,{
      method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({stage:next})
    });
    const d=await response.json(); if(!response.ok) throw new Error(d.error||(translations[currentLanguage] || translations.en).tracking_update_error);
    await loadTracking(trackingToken);
  }catch(e){alert(e.message || (translations[currentLanguage] || translations.en).tracking_update_error);}
}

function featureTokenValue(){
  const input=document.getElementById("featureToken");
  return normalizeTrackingToken((input && input.value) || getSavedUserToken());
}

function renderEffort(d){
  document.getElementById("effortNoData").style.display="none";
  document.getElementById("effortContent").style.display="block";
  document.getElementById("effortScore").textContent=d.score;
  document.getElementById("effortVisits").textContent=d.visit_count;
  document.getElementById("effortUnnecessary").textContent=d.unnecessary_visits;
  document.getElementById("effortWait").textContent=d.waiting_minutes < 60 ? `${d.waiting_minutes} min` : `${Math.floor(d.waiting_minutes/60)}h ${d.waiting_minutes%60}m`;
  document.getElementById("effortRepeat").textContent=d.repeated_processes;
}

function renderLotTrace(rows){
  const box=document.getElementById("lotTraceTimeline");
  box.innerHTML="";
  rows.forEach((r,i)=>{
    const item=document.createElement("div"); item.className="trace-item";
    const dot=document.createElement("div"); dot.className="trace-dot"+(r.status==="Completed"?" done":"")+(r.status==="Rejected"?" rejected":""); dot.textContent=r.status==="Completed"?"✓":(r.status==="Rejected"?"!":i+1);
    const mid=document.createElement("div"); mid.innerHTML=`<div class="trace-name">${escapeHtml(r.name)}</div><div class="trace-detail">${escapeHtml(r.detail||"")}</div>`;
    const st=document.createElement("div"); st.className="trace-status"+(r.status==="Completed"?" done":"")+(r.status==="Rejected"?" rejected":""); st.textContent=lotTraceStatusText(r.status);
    item.appendChild(dot); item.appendChild(mid); item.appendChild(st); box.appendChild(item);
  });
}

function escapeHtml(value){
  return String(value==null?"":value).replace(/[&<>'"]/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[ch]));
}
function lotTraceStatusText(status){
  const t=translations[currentLanguage] || translations.en;
  return status==="Completed"?t.lot_completed:(status==="Rejected"?t.lot_rejected:t.lot_pending);
}

async function loadSmartFeatures(tokenOverride=null){
  const token=normalizeTrackingToken(tokenOverride || featureTokenValue());
  if(!token){
    document.getElementById("effortNoData").style.display="block";
    document.getElementById("effortContent").style.display="none";
    document.getElementById("lotTraceEmpty").style.display="block";
    document.getElementById("lotTraceContent").style.display="none";
    document.getElementById("rejectionNoData").style.display="block";
    return;
  }
  document.getElementById("featureToken").value=token;
  localStorage.setItem("kisanGatiUserToken",token);
  try{
    const [effortRes,traceRes,rejectionRes]=await Promise.all([
      fetch(`/api/effort/${token}`), fetch(`/api/lot-trace/${token}`), fetch(`/api/rejection/${token}`)
    ]);
    const effort=await effortRes.json(); const trace=await traceRes.json(); const rej=await rejectionRes.json();
    if(!effortRes.ok) throw new Error(effort.error || "Farmer token not found.");
    renderEffort(effort);
    if(traceRes.ok){
      document.getElementById("lotTraceEmpty").style.display="none";
      document.getElementById("lotTraceContent").style.display="block";
      renderLotTrace(trace.trace || []);
    }
    renderRejectionHistory(rej.rejections || []);
  }catch(e){
    alert(e.message || "Unable to load the feature data.");
  }
}

async function recordFarmerVisit(){
  const token=featureTokenValue();
  if(!token){alert((translations[currentLanguage]||translations.en).valid_token);return;}
  try{
    const r=await fetch(`/api/effort/${token}/visit`,{method:"POST"}); const d=await r.json();
    if(!r.ok) throw new Error(d.error||"Unable to record visit.");
    renderEffort(d);
  }catch(e){alert(e.message);}
}

async function updateLotTrace(){
  const token=featureTokenValue(); if(!token){alert((translations[currentLanguage]||translations.en).valid_token);return;}
  const step=document.getElementById("lotTraceStep").value;
  const status=document.getElementById("lotTraceStatus").value;
  const detail=document.getElementById("lotTraceDetail").value.trim();
  try{
    const r=await fetch(`/api/lot-trace/${token}/update`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({step,status,detail})});
    const d=await r.json(); if(!r.ok) throw new Error(d.error||"Unable to update lot trace.");
    renderLotTrace(d.trace||[]); document.getElementById("lotTraceDetail").value="";
  }catch(e){alert(e.message);}
}

async function saveRejection(){
  const token=featureTokenValue(); if(!token){alert((translations[currentLanguage]||translations.en).valid_token);return;}
  const select=document.getElementById("rejectionReason"); const reason=select.value;
  const guidance=document.getElementById("rejectionGuidance").value.trim();
  if(!reason || !guidance){alert((translations[currentLanguage]||translations.en).rejection_required);return;}
  try{
    const r=await fetch(`/api/rejection/${token}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reason,guidance})});
    const d=await r.json(); if(!r.ok) throw new Error(d.error||"Unable to save rejection.");
    document.getElementById("rejectionGuidance").value="";
    alert((translations[currentLanguage]||translations.en).rejection_saved);
    const h=await fetch(`/api/rejection/${token}`); const hd=await h.json(); renderRejectionHistory(hd.rejections||[]);
  }catch(e){alert(e.message);}
}

function renderRejectionHistory(rows){
  const no=document.getElementById("rejectionNoData"); const box=document.getElementById("rejectionHistory");
  box.innerHTML="";
  if(!rows.length){no.style.display="block";return;}
  no.style.display="none";
  rows.slice(0,5).forEach(r=>{
    const item=document.createElement("div"); item.className="rejection-item";
    item.innerHTML=`<b>${escapeHtml(r.reason)}</b><p>${escapeHtml(r.guidance)}</p>`;
    box.appendChild(item);
  });
}


async function loadFarmerTraceAndRejections(token){
  try{
    const [tr,rr]=await Promise.all([fetch(`/api/lot-trace/${token}`),fetch(`/api/rejection/${token}`)]);
    const trace=await tr.json(); const rej=await rr.json();
    const tb=document.getElementById("farmerLotTraceTimeline"); tb.innerHTML="";
    (trace.trace||[]).forEach(row=>{const d=document.createElement("div");d.className="trace-item";d.innerHTML=`<b>${escapeHtml(row.step_name)}</b><span class="badge">${escapeHtml(row.status)}</span><small>${escapeHtml(row.detail||"")} • ${escapeHtml(row.updated_at||"")}</small>`;tb.appendChild(d);});
    const rb=document.getElementById("farmerRejectionHistory"); rb.innerHTML="";
    (rej.rejections||[]).forEach(row=>{const d=document.createElement("div");d.className="rejection-item";d.innerHTML=`<b>${escapeHtml(row.reason)}</b><p>${escapeHtml(row.guidance)}</p><small>${escapeHtml(row.created_at||"")}</small>`;rb.appendChild(d);});
    if(!(rej.rejections||[]).length) rb.innerHTML='<p class="form-help">No quality rejection has been recorded for this lot.</p>';
  }catch(e){}
}
async function loadAdminSummary(){
  try{const r=await fetch('/api/admin/summary');if(!r.ok)return;const d=await r.json();document.getElementById('adminFarmerCount').textContent=d.farmers;document.getElementById('adminQueueToken').textContent=d.current_token;document.getElementById('adminTrackedLots').textContent=d.tracked_lots;document.getElementById('adminRejections').textContent=d.rejections;}catch(e){}
}

async function simulateQueue(){
  try{
    const response = await fetch("/api/queue/next", {method:"POST"});
    const d = await response.json();
    const userToken = getSavedUserToken();
    let msg = `Queue updated. The centre is now serving ${d.current}.`;

    if(userToken){
      const m = userToken.match(/P(\\d+)/);
      if(m){
        const ahead = Math.max(0, parseInt(m[1],10) - parseInt(d.current.slice(1),10) - 1);
        msg += ahead === 0 ? " Your token is next." : ` You have ${ahead} tokens ahead of you.`;
      }
    }

    alert(msg);
    refreshQueueDisplay();
  }catch(e){
    alert("Unable to update the queue right now.");
  }
}

async function refreshQueueDisplay(){
  try{
    const response = await fetch("/api/queue");
    const d = await response.json();
    const tokenBoxes = document.querySelectorAll(".token");
    if(tokenBoxes.length) tokenBoxes[0].textContent = d.current;
  }catch(e){}
}
document.addEventListener("DOMContentLoaded", () => {
  applyLanguage(localStorage.getItem("kisanGatiLanguage") || "{{language}}");
  saveDetectedToken();
  const savedToken = getSavedUserToken();
  if(savedToken && document.getElementById("trackingToken")){ loadTracking(savedToken); }
  if(savedToken && document.getElementById("featureToken")){ document.getElementById("featureToken").value=savedToken; loadSmartFeatures(savedToken); }
  loadWeather();
  refreshQueueDisplay();
  if(document.getElementById("adminConsole")) loadAdminSummary();
});

function toggleAI(){
  const panel = document.getElementById("aiPanel");
  panel.style.display = panel.style.display === "block" ? "none" : "block";
  if(panel.style.display === "block") document.getElementById("aiInput").focus();
}
function addAIMessage(text, cls){
  const body = document.getElementById("aiBody");
  const div = document.createElement("div");
  div.className = "ai-msg " + cls;
  div.textContent = text;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
}
async function sendAI(textFromVoice=null){
  const input = document.getElementById("aiInput");
  const text = (textFromVoice || input.value).trim();
  if(!text) return;

  addAIMessage(text, "ai-user");
  input.value = "";
  document.getElementById("aiStatus").textContent = "Thinking...";

  try{
    let queueData = null;
    try{
      const qResponse = await fetch("/api/queue");
      queueData = await qResponse.json();
    }catch(e){}

    const response = await fetch("/ai_assistant", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        message:text,
        language:currentLanguage,
        user_token:getSavedUserToken(),
        weather:latestWeather,
        queue:queueData
      })
    });

    if(!response.ok) throw new Error("Assistant request failed");
    const data = await response.json();

    if(data.user_token) localStorage.setItem("kisanGatiUserToken", data.user_token);

    addAIMessage(data.reply || "Sorry, I could not answer that.", "ai-bot");
    speakAI(data.reply || "");
  }catch(e){
    addAIMessage(
      "I could not connect to the KisanGati assistant. Please check that the Flask server is running.",
      "ai-bot"
    );
  }

  document.getElementById("aiStatus").textContent = "Ready";
}
let recognition = null;
function startVoice(){
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = document.getElementById("micButton");
  const status = document.getElementById("aiStatus");
  if(!SpeechRecognition){
    status.textContent = "Voice recognition is not supported. Try Chrome or Edge.";
    return;
  }
  if(recognition){ recognition.stop(); recognition=null; mic.classList.remove("listening"); status.textContent="Ready"; return; }
  recognition = new SpeechRecognition();
  recognition.lang = getSpeechLanguage();
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.onstart = () => { mic.classList.add("listening"); status.textContent="🎤 Listening... Speak now"; };
  recognition.onresult = event => { const text=event.results[0][0].transcript; document.getElementById("aiInput").value=text; sendAI(text); };
  recognition.onerror = event => { status.textContent="Voice error: "+event.error; };
  recognition.onend = () => { mic.classList.remove("listening"); recognition=null; if(status.textContent.includes("Listening")) status.textContent="Ready"; };
  recognition.start();
}
function getSpeechLanguage(){
  const map={en:"en-IN",hi:"hi-IN",bn:"bn-IN",ta:"ta-IN",as:"as-IN",te:"te-IN",mr:"mr-IN",gu:"gu-IN",kn:"kn-IN",ml:"ml-IN",or:"or-IN",pa:"pa-IN"};
  return map[typeof currentLanguage!=="undefined" ? currentLanguage : "en"] || "en-IN";
}
function speakAI(text){
  if(!("speechSynthesis" in window) || !text) return;
  window.speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(text);
  u.lang=getSpeechLanguage();
  u.rate=0.95;
  window.speechSynthesis.speak(u);
}

</script>

<!-- AI FARM ASSISTANT -->
<div id="aiPanel" class="ai-panel">
  <div class="ai-head">
    <strong>🤖 KisanGati AI Assistant</strong>
    <button type="button" onclick="toggleAI()">✕</button>
  </div>
  <div id="aiBody" class="ai-body">
    <div class="ai-msg ai-bot">Namaste! 🌾 I am your KisanGati AI assistant.<br><br>Ask me about crop procurement, queue status, slot booking, weather, farming tips, or payment status. You can type or use 🎤 voice.</div>
  </div>
  <div id="aiStatus" class="ai-status">Ready</div>
  <div class="ai-input">
    <input id="aiInput" type="text" placeholder="Ask the AI assistant..." onkeydown="if(event.key==='Enter')sendAI()">
    <button id="micButton" class="ai-mic" type="button" onclick="startVoice()">🎤</button>
    <button type="button" onclick="sendAI()">➤</button>
  </div>
</div>
<button class="ai-fab" type="button" onclick="toggleAI()" title="AI Assistant">🤖</button>

</body>
</html>
"""

SLOTS = [
    "10:00 AM - 11:00 AM",
    "11:00 AM - 12:00 PM",
    "01:00 PM - 02:00 PM",
    "02:00 PM - 03:00 PM"
]

# Consistent demo queue state while the Flask app is running.
CURRENT_QUEUE_TOKEN = 97

def db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS farmers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE,
        name TEXT,
        mobile TEXT,
        farmer_id TEXT,
        crop TEXT,
        quantity REAL,
        slot TEXT,
        status TEXT,
        created_at TEXT,
        bank_name TEXT,
        account_holder TEXT,
        account_number TEXT,
        ifsc_code TEXT,
        tracking_id TEXT
    )""")

    # Backward-compatible migration for older KisanGati databases.
    existing = {row[1] for row in conn.execute("PRAGMA table_info(farmers)").fetchall()}
    new_columns = {
        "bank_name": "TEXT",
        "account_holder": "TEXT",
        "account_number": "TEXT",
        "ifsc_code": "TEXT",
        "tracking_id": "TEXT"
    }
    for column, definition in new_columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE farmers ADD COLUMN {column} {definition}")

    conn.execute("""CREATE TABLE IF NOT EXISTS shipment_tracking(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE,
        tracking_id TEXT UNIQUE,
        stage TEXT NOT NULL DEFAULT 'At Procurement Centre',
        location_name TEXT NOT NULL DEFAULT 'Procurement Centre',
        latitude REAL,
        longitude REAL,
        accuracy REAL,
        last_updated TEXT,
        gps_active INTEGER NOT NULL DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS tracking_updates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT,
        stage TEXT,
        location_name TEXT,
        latitude REAL,
        longitude REAL,
        accuracy REAL,
        updated_at TEXT
    )""")

    # Farmer Effort Index: records observable centre visits and process repetitions.
    # The index is a transparent demo metric based only on events recorded by KisanGati.
    conn.execute("""CREATE TABLE IF NOT EXISTS farmer_effort(
        token TEXT PRIMARY KEY,
        visit_count INTEGER NOT NULL DEFAULT 1,
        first_registered_at TEXT,
        first_quality_at TEXT,
        last_updated TEXT
    )""")

    # Lot Trace: one digital trail from farmer registration to quality, procurement and payment.
    conn.execute("""CREATE TABLE IF NOT EXISTS lot_trace(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT,
        step_key TEXT,
        step_name TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        detail TEXT,
        updated_at TEXT
    )""")

    # Explainable Rejection: stores the reason and actionable guidance for every rejection.
    conn.execute("""CREATE TABLE IF NOT EXISTS rejection_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT,
        reason TEXT,
        guidance TEXT,
        created_at TEXT
    )""")

    # Give existing farmers a stable tracking ID and a tracking record.
    farmers = conn.execute("SELECT token, tracking_id FROM farmers").fetchall()
    for token, tracking_id in farmers:
        tracking_id = tracking_id or f"KG-{token}"
        conn.execute("UPDATE farmers SET tracking_id=? WHERE token=?", (tracking_id, token))
        now = datetime.now().isoformat()
        conn.execute("""INSERT OR IGNORE INTO shipment_tracking
            (token,tracking_id,stage,location_name,last_updated)
            VALUES (?,?,?,?,?)""", (token,tracking_id,"At Procurement Centre","Procurement Centre",now))
        conn.execute("""INSERT OR IGNORE INTO farmer_effort(token,visit_count,first_registered_at,last_updated)
            VALUES (?,?,?,?)""", (token,1,now,now))
        if conn.execute("SELECT COUNT(*) FROM lot_trace WHERE token=?", (token,)).fetchone()[0] == 0:
            conn.execute("""INSERT INTO lot_trace(token,step_key,step_name,status,detail,updated_at) VALUES
                (?,?,?,?,?,?), (?,?,?,?,?,?), (?,?,?,?,?,?), (?,?,?,?,?,?)""", (
                token,"farmer","Farmer Registration","Completed","Digital registration created",now,
                token,"quality","Quality Check","Pending","Awaiting quality check",now,
                token,"procurement","Procurement","Pending","Awaiting procurement",now,
                token,"payment","Payment","Pending","Awaiting payment",now))

    conn.commit()
    return conn


from urllib.parse import quote
from urllib.request import urlopen

_TRANSLATION_CACHE = {}
def translate_ai_reply(text, target_language):
    if not text or target_language == "en":
        return text
    key=(target_language,text)
    if key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[key]
    try:
        url=("https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl="
             + quote(target_language) + "&dt=t&q=" + quote(text))
        with urlopen(url, timeout=4) as response:
            data=json.loads(response.read().decode("utf-8"))
        translated="".join(part[0] for part in data[0] if part and part[0])
        if translated:
            _TRANSLATION_CACHE[key]=translated
            return translated
    except Exception:
        pass
    return text

@app.route("/ai_assistant", methods=["POST"])
def ai_assistant():
    """Data-aware KisanGati assistant.

    Weather comes from the browser's latest Open-Meteo reading.
    Token/registration information comes directly from SQLite.
    Queue information comes from the live demo queue state.
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    language = (data.get("language") or "en").strip()
    if language not in TRANSLATIONS:
        language = "en"
    if not message:
        return jsonify({"reply": "Please tell me what you want to know."})

    q = message.lower()
    weather = data.get("weather") or {}
    user_token = (data.get("user_token") or "").strip().upper()

    conn = db()

    # Resolve the farmer token saved in this browser.
    farmer = None
    if user_token:
        farmer = conn.execute(
            "SELECT token,name,crop,quantity,slot,status FROM farmers WHERE token=?",
            (user_token,)
        ).fetchone()

    # Demo fallback: most recent registration.
    if farmer is None:
        farmer = conn.execute(
            "SELECT token,name,crop,quantity,slot,status FROM farmers ORDER BY id DESC LIMIT 1"
        ).fetchone()

    global CURRENT_QUEUE_TOKEN
    current_num = CURRENT_QUEUE_TOKEN
    current_token = f"P{current_num:03d}"

    # Greetings
    if any(x in q for x in [
        "hello", "hi", "hey", "namaste", "good morning", "good afternoon",
        "good evening", "नमस्ते", "हैलो", "হ্যালো", "নমস্কাৰ"
    ]):
        reply = (
            "Namaste! 🌾 I am KisanGati AI. I can directly answer questions about "
            "your token and queue position, current weather, slot availability, "
            "registration status, procurement, payment, and farming."
        )

    # Exact weather
    elif any(x in q for x in [
        "weather", "rain", "temperature", "humidity", "wind", "forecast",
        "बारिश", "मौसम", "तापमान", "বৃষ্টি", "আবহাওয়া", "தமிழ் வானிலை",
        "மழை", "வெப்பநிலை", "বৰষুণ", "বতৰ", "তাপমাত্ৰা"
    ]):
        if weather.get("temperature") is not None:
            temp = weather.get("temperature")
            humidity = weather.get("humidity")
            wind = weather.get("wind")
            rain = weather.get("rain_chance")
            condition = weather.get("condition") or "Current conditions"
            location = weather.get("location") or "your current location"

            reply = (
                f"🌦️ Current weather at {location}: {condition}. "
                f"Temperature: {temp}°C. Humidity: {humidity}%. "
                f"Wind: {wind} km/h. Chance of rain: {rain}%. "
            )

            try:
                temp_n = float(temp)
                rain_n = float(rain)
                wind_n = float(wind)
                code = int(weather.get("code", -1))
            except (TypeError, ValueError):
                temp_n, rain_n, wind_n, code = 0, 0, 0, -1

            if code in (95, 96, 99):
                reply += "⚠️ Thunderstorm risk: avoid working in open fields."
            elif rain_n >= 70:
                reply += "🌧️ Rain is likely, so consider delaying spraying, harvesting, or transport."
            elif temp_n >= 38:
                reply += "☀️ It is quite hot; stay hydrated and avoid heavy work during peak heat."
            elif wind_n >= 40:
                reply += "💨 Strong winds are possible; secure crops and equipment."
            else:
                reply += "✅ Conditions are generally suitable for normal farm activity."
        else:
            reply = (
                "I don't have the latest weather reading yet. Please allow location access "
                "in the browser and ask me for the weather again."
            )

    # Token / queue
    elif any(x in q for x in [
        "token", "queue", "waiting", "turn", "position", "ahead",
        "कतार", "टोकन", "प्रतीक्षा", "मेरी बारी", "कितने आगे",
        "সারি", "টোকেন", "অপেক্ষা", "வரிசை", "டோக்கன்",
        "শাৰী", "ಕ್ಯೂ"
    ]):
        token_match = re.search(r"\bP\s*([0-9]{3})\b", message, re.IGNORECASE)
        if token_match:
            requested_token = f"P{int(token_match.group(1)):03d}"
            row = conn.execute(
                "SELECT token,name,crop,quantity,slot,status FROM farmers WHERE token=?",
                (requested_token,)
            ).fetchone()
            farmer = row if row else (requested_token, None, None, None, None, None)

        if farmer:
            farmer_token = farmer[0]
            try:
                farmer_num = int(farmer_token[1:])
            except (ValueError, TypeError):
                farmer_num = None

            if farmer_num is None:
                reply = f"Your token is {farmer_token}."
            elif farmer_num <= current_num:
                reply = (
                    f"🎟️ Your token is {farmer_token}. The centre is currently serving "
                    f"{current_token}. Your token has already reached or passed the current queue position."
                )
            else:
                ahead = max(0, farmer_num - current_num - 1)
                if ahead == 0:
                    reply = (
                        f"🎟️ Your token is {farmer_token}. The centre is serving "
                        f"{current_token}, so you are next."
                    )
                else:
                    reply = (
                        f"🎟️ Your token is {farmer_token}. Currently serving: {current_token}. "
                        f"There are exactly {ahead} tokens ahead of you."
                    )
        else:
            reply = (
                f"The centre is currently serving {current_token}. "
                "I don't have a farmer token saved for you yet. Register first and I can "
                "give you your exact queue position."
            )

    # Slot availability
    elif any(x in q for x in [
        "slot", "booking", "book", "available", "availability",
        "स्लॉट", "बुक", "उपलब्ध", "বুকিং", "স্লট", "ஸ்லாட்",
        "ச்லாட்", "শাৰী", "ಸ್ಲಾಟ್"
    ]):
        rows = conn.execute("SELECT slot, COUNT(*) FROM farmers GROUP BY slot").fetchall()
        counts = {row[0]: row[1] for row in rows}
        available = []
        for slot in SLOTS:
            remaining = max(0, 10 - counts.get(slot, 0))
            if remaining:
                available.append(f"{slot} ({remaining} spots left)")

        reply = (
            "📅 Available procurement slots: " + "; ".join(available) + "."
            if available else
            "All procurement slots are currently full."
        )

    # Personal registration / booking status
    elif any(x in q for x in [
        "my registration", "my booking", "my status", "registration status",
        "booking status", "मेरी बुकिंग", "मेरी स्थिति", "पंजीकरण की स्थिति",
        "আমার বুকিং", "আমার স্ট্যাটাস"
    ]):
        if farmer:
            reply = (
                f"Your registration status is {farmer[5]}. "
                f"Token: {farmer[0]}. Crop: {farmer[2]}. "
                f"Quantity: {farmer[3]} quintals. Slot: {farmer[4]}."
            )
        else:
            reply = "There is no farmer registration in the database yet."

    # Procurement
    elif any(x in q for x in [
        "procurement", "purchase", "quality", "weighing", "weigh",
        "crop purchase", "खरीद", "गुणवत्ता", "वजन", "ক্ৰয়", "ওজন",
        "கொள்முதல்", "எடை"
    ]):
        if farmer:
            reply = (
                f"For token {farmer[0]}, the recorded registration status is {farmer[5]}. "
                f"Crop: {farmer[2]}. Quantity: {farmer[3]} quintals. "
                "The workflow is booking → arrival → queue → quality check → weighing → procurement → payment."
            )
        else:
            reply = (
                "KisanGati tracks booking, arrival, queue, quality check, weighing, "
                "procurement and payment."
            )

    # Payment
    elif any(x in q for x in [
        "payment", "paid", "money", "amount", "payment status",
        "पैसा", "भुगतान", "राशि", "পেমেন্ট", "টাকা", "பணம்", "கட்டணம்"
    ]):
        if farmer:
            reply = (
                f"For token {farmer[0]}, the current recorded status is {farmer[5]}. "
                "The demo dashboard is the source of truth for the payment amount and processing state."
            )
        else:
            reply = "Register a farmer first so I can identify the relevant payment record."

    # Farming advice
    elif any(x in q for x in [
        "farming", "farmer", "crop", "paddy", "rice", "wheat", "maize",
        "फसल", "खेती", "धान", "गेहूं", "मक्का", "শস্য", "ধান", "গম",
        "கிருஷி", "பயிர்", "விவசாயம்"
    ]):
        if any(x in q for x in ["paddy", "rice", "धान", "ধান", "நெல்"]):
            reply = (
                "🌾 For paddy/rice, maintain suitable soil moisture for the crop stage, "
                "avoid unnecessary waterlogging, and monitor regularly for pests and disease. "
                "For procurement, bring your token and follow the booked slot."
            )
        elif any(x in q for x in ["wheat", "गेहूं", "গম"]):
            reply = (
                "🌾 For wheat, irrigate according to the crop stage, control weeds, "
                "monitor for disease, and avoid unnecessary irrigation close to harvest."
            )
        elif any(x in q for x in ["maize", "मक्का"]):
            reply = (
                "🌽 For maize, maintain suitable soil moisture, monitor weeds and pests, "
                "and avoid waterlogging."
            )
        else:
            reply = (
                "🌱 Tell me the crop name and your question. I can help with irrigation, "
                "pests, disease, harvesting, or procurement."
            )

    # Help
    elif any(x in q for x in ["help", "what can you do", "क्या कर सकते", "সাহায্য", "உதவி"]):
        reply = (
            "I can answer directly from the KisanGati demo. Try asking: "
            "'What is the current weather?', 'What is my token?', "
            "'How many tokens are ahead of me?', 'Which slots are available?', "
            "'What is my registration status?', or ask a crop question."
        )

    else:
        reply = (
            "I didn't understand that. Ask me directly about weather, your token, "
            "queue position, available slots, registration, procurement, payment, or farming."
        )

    conn.close()
    # The assistant's internal logic stays data-aware, while the final answer
    # is translated into the language currently selected in the website.
    reply = translate_ai_reply(reply, language)
    return jsonify({
        "reply": reply,
        "current_token": current_token,
        "user_token": farmer[0] if farmer else None,
        "language": language
    })

def _render_portal(role):
    conn = db()
    farmers = conn.execute(
        "SELECT token,name,crop,quantity,slot,status FROM farmers ORDER BY id DESC LIMIT 10"
    ).fetchall()
    slots = [(s, conn.execute("SELECT COUNT(*) FROM farmers WHERE slot=?", (s,)).fetchone()[0]) for s in SLOTS]
    conn.close()
    language = request.args.get("lang", session.get("language", "en"))
    if language not in TRANSLATIONS: language = "en"
    session["language"] = language
    return render_template_string(HTML, farmers=farmers, slots=slots,
                                  languages=TRANSLATIONS, language=language,
                                  trans=TRANSLATIONS[language], role=role,
                                  translations_json=json.dumps(TRANSLATIONS, ensure_ascii=False))

@app.route("/")
def home():
    if session.get("role") == "farmer": return redirect(url_for("farmer_page"))
    if session.get("role") == "admin": return redirect(url_for("admin_page"))
    language = request.args.get("lang", "en")
    if language not in LOGIN_TRANSLATIONS: language = "en"
    return render_template_string(LOGIN_HTML, language=language,
                                  login_translations_json=json.dumps(LOGIN_TRANSLATIONS, ensure_ascii=False))

@app.route("/farmer")
@login_required
def farmer_page():
    if session.get("role") != "farmer": return redirect(url_for("admin_page"))
    return _render_portal("farmer")

@app.route("/admin")
@login_required
def admin_page():
    if session.get("role") != "admin": return redirect(url_for("farmer_page"))
    return _render_portal("admin")

@app.route("/login", methods=["POST"])
def login():
    role=request.form.get("role", "farmer")
    language=request.form.get("language", "en")
    if language not in LOGIN_TRANSLATIONS: language = "en"
    if role == "admin":
        username=request.form.get("username", "").strip()
        password=request.form.get("password", "")
        expected_user=os.getenv("ADMIN_USERNAME", "admin")
        expected_pass=os.getenv("ADMIN_PASSWORD", "admin123")
        if hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_pass):
            session.clear(); session["role"]="admin"; session["language"]=language
            return redirect(url_for("admin_page"))
        flash(LOGIN_TRANSLATIONS[language]["invalid_admin"])
        return redirect(url_for("home", lang=language))
    mobile=re.sub(r"\D", "", request.form.get("mobile", ""))
    token=re.sub(r"\s", "", request.form.get("token", "")).upper()
    conn=db(); row=conn.execute("SELECT token FROM farmers WHERE token=? AND mobile=?",(token,mobile)).fetchone(); conn.close()
    if not row:
        flash(LOGIN_TRANSLATIONS[language]["invalid_farmer"])
        return redirect(url_for("home", lang=language))
    session.clear(); session["role"]="farmer"; session["farmer_token"]=token; session["language"]=language
    return redirect(url_for("farmer_page"))

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.route("/new-farmer")
def new_farmer():
    # Open the same farmer registration page without granting admin access.
    session["role"]="farmer"
    return redirect(url_for("farmer_page") + "#register")

@app.route("/register", methods=["POST"])
def register():
    conn = db()
    count = conn.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
    token = f"P{100 + count + 1:03d}"

    name = request.form.get("name", "").strip()
    mobile = re.sub(r"\D", "", request.form.get("mobile", ""))
    farmer_id = request.form.get("farmer_id", "").strip()
    crop = request.form.get("crop", "").strip()
    quantity = request.form.get("quantity", "").strip()
    slot = request.form.get("slot", "").strip()
    bank_name = request.form.get("bank_name", "").strip()
    account_holder = request.form.get("account_holder", "").strip()
    account_number = re.sub(r"\D", "", request.form.get("account_number", ""))
    ifsc_code = request.form.get("ifsc_code", "").strip().upper()

    language = request.form.get("language", "en")
    if language not in TRANSLATIONS: language = "en"

    if not re.fullmatch(r"\d{10}", mobile):
        flash(TRANSLATIONS[language]["valid_mobile"])
        conn.close()
        return redirect(url_for("home", lang=language) + "#register")
    if not re.fullmatch(r"\d{9,18}", account_number):
        flash(TRANSLATIONS[language]["valid_account"])
        conn.close()
        return redirect(url_for("home", lang=language) + "#register")
    if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", ifsc_code):
        flash(TRANSLATIONS[language]["valid_ifsc"])
        conn.close()
        return redirect(url_for("home", lang=language) + "#register")

    tracking_id = f"KG-{token}"
    conn.execute("""INSERT INTO farmers
        (token,name,mobile,farmer_id,crop,quantity,slot,status,created_at,
         bank_name,account_holder,account_number,ifsc_code,tracking_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (token, name, mobile, farmer_id, crop, quantity, slot,
         "Booking Confirmed", datetime.now().isoformat(), bank_name,
         account_holder, account_number, ifsc_code, tracking_id))
    now = datetime.now().isoformat()
    conn.execute("""INSERT INTO shipment_tracking
        (token,tracking_id,stage,location_name,last_updated,gps_active)
        VALUES (?,?,?,?,?,0)""",
        (token, tracking_id, "At Procurement Centre", "Procurement Centre", now))
    conn.execute("""INSERT INTO farmer_effort(token,visit_count,first_registered_at,last_updated)
        VALUES (?,?,?,?)""", (token,1,now,now))
    conn.execute("""INSERT INTO lot_trace(token,step_key,step_name,status,detail,updated_at) VALUES
        (?,?,?,?,?,?), (?,?,?,?,?,?), (?,?,?,?,?,?), (?,?,?,?,?,?)""", (
        token,"farmer","Farmer Registration","Completed","Digital registration created",now,
        token,"quality","Quality Check","Pending","Awaiting quality check",now,
        token,"procurement","Procurement","Pending","Awaiting procurement",now,
        token,"payment","Payment","Pending","Awaiting payment",now))
    conn.commit()
    conn.close()
    session.clear(); session["role"]="farmer"; session["farmer_token"]=token; session["language"]=language
    flash(TRANSLATIONS[language]["success"].format(token=token) + TRANSLATIONS[language]["tracking_id_success"].format(tracking_id=tracking_id))
    return redirect(url_for("farmer_page", lang=language) + "#tracking")

# ---------------- LIVE SHIPMENT / GPS TRACKING ----------------
TRACKING_STAGES = [
    "At Procurement Centre",
    "Quality Check",
    "Weighing",
    "Processing",
    "Shipped",
    "In Transit",
    "Delivered"
]

STAGE_LOCATIONS = {
    "At Procurement Centre": "Procurement Centre",
    "Quality Check": "Quality Check Unit",
    "Weighing": "Weighing Bay",
    "Processing": "Processing Unit",
    "Shipped": "Dispatch Centre",
    "In Transit": "Live GPS Location",
    "Delivered": "Destination Centre"
}

@app.route("/api/tracking/<token>")
@login_required
def tracking_status(token):
    if not token_access_allowed(token):
        return jsonify({"error":"You can only view your own farmer records."}), 403
    token = token.strip().upper()
    conn = db()
    row = conn.execute("""SELECT f.token,f.name,f.crop,f.quantity,f.status,f.tracking_id,
                              t.stage,t.location_name,t.latitude,t.longitude,t.accuracy,
                              t.last_updated,t.gps_active
                       FROM farmers f JOIN shipment_tracking t ON f.token=t.token
                       WHERE f.token=?""", (token,)).fetchone()
    history = conn.execute("""SELECT stage,location_name,latitude,longitude,updated_at
                             FROM tracking_updates WHERE token=? ORDER BY id DESC LIMIT 20""", (token,)).fetchall()
    conn.close()
    if not row:
        return jsonify({"error":"Tracking token not found."}), 404
    return jsonify({
        "token":row[0], "farmer":row[1], "crop":row[2], "quantity":row[3],
        "status":row[4], "tracking_id":row[5], "stage":row[6],
        "location":row[7], "latitude":row[8], "longitude":row[9],
        "accuracy":row[10], "last_updated":row[11], "gps_active":bool(row[12]),
        "history":[{"stage":h[0],"location":h[1],"latitude":h[2],"longitude":h[3],"updated_at":h[4]} for h in history]
    })

@app.route("/api/tracking/<token>/location", methods=["POST"])
@admin_required
def tracking_location(token):
    token = token.strip().upper()
    data = request.get_json(silent=True) or {}
    try:
        lat = float(data.get("latitude"))
        lon = float(data.get("longitude"))
        accuracy = float(data.get("accuracy")) if data.get("accuracy") is not None else None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error":"Valid latitude and longitude are required."}), 400

    now = datetime.now().isoformat()
    conn = db()
    exists = conn.execute("SELECT 1 FROM shipment_tracking WHERE token=?", (token,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"error":"Tracking token not found."}), 404
    conn.execute("""UPDATE shipment_tracking
                   SET stage='In Transit', location_name='Live GPS Location',
                       latitude=?, longitude=?, accuracy=?, last_updated=?, gps_active=1
                   WHERE token=?""", (lat,lon,accuracy,now,token))
    conn.execute("""INSERT INTO tracking_updates
                   (token,stage,location_name,latitude,longitude,accuracy,updated_at)
                   VALUES (?,?,?,?,?,?,?)""", (token,"In Transit","Live GPS Location",lat,lon,accuracy,now))
    conn.commit(); conn.close()
    return jsonify({"ok":True,"stage":"In Transit","location":"Live GPS Location",
                    "latitude":lat,"longitude":lon,"accuracy":accuracy,"last_updated":now})

@app.route("/api/tracking/<token>/stop", methods=["POST"])
@admin_required
def tracking_stop(token):
    token = token.strip().upper()
    conn = db()
    cur = conn.execute("UPDATE shipment_tracking SET gps_active=0 WHERE token=?", (token,))
    conn.commit(); conn.close()
    if cur.rowcount == 0:
        return jsonify({"error":"Tracking token not found."}), 404
    return jsonify({"ok":True,"gps_active":False})

@app.route("/api/tracking/<token>/stage", methods=["POST"])
@admin_required
def tracking_stage(token):
    token = token.strip().upper()
    data = request.get_json(silent=True) or {}
    stage = (data.get("stage") or "").strip()
    if stage not in TRACKING_STAGES:
        return jsonify({"error":"Invalid tracking stage."}), 400
    location = (data.get("location") or STAGE_LOCATIONS[stage]).strip()
    now = datetime.now().isoformat()
    conn = db()
    exists = conn.execute("SELECT 1 FROM shipment_tracking WHERE token=?", (token,)).fetchone()
    if not exists:
        conn.close(); return jsonify({"error":"Tracking token not found."}), 404
    conn.execute("""UPDATE shipment_tracking SET stage=?,location_name=?,last_updated=?,gps_active=0 WHERE token=?""",
                 (stage,location,now,token))
    conn.execute("""INSERT INTO tracking_updates(token,stage,location_name,latitude,longitude,accuracy,updated_at)
                   SELECT token,stage,location_name,latitude,longitude,accuracy,?
                   FROM shipment_tracking WHERE token=?""", (now,token))

    # Keep the Lot Trace synchronized with the operational tracking stage.
    if stage == "Quality Check":
        conn.execute("UPDATE lot_trace SET status='Completed',detail='Quality check recorded',updated_at=? WHERE token=? AND step_key='quality'",(now,token))
        conn.execute("UPDATE farmer_effort SET first_quality_at=COALESCE(first_quality_at,?),last_updated=? WHERE token=?",(now,now,token))
    elif stage in ("Processing","Shipped","In Transit","Delivered"):
        conn.execute("UPDATE lot_trace SET status='Completed',detail='Procurement progress recorded',updated_at=? WHERE token=? AND step_key='procurement'",(now,token))
    conn.commit(); conn.close()
    return jsonify({"ok":True,"stage":stage,"location":location,"last_updated":now})


# ---------------- FARMER EFFORT / LOT TRACE / EXPLAINABLE REJECTION ----------------

def _effort_metrics(conn, token):
    row = conn.execute("SELECT visit_count,first_registered_at,first_quality_at FROM farmer_effort WHERE token=?", (token,)).fetchone()
    if not row:
        return None
    visit_count = int(row[0] or 1)
    registered = row[1]
    quality_at = row[2]
    try:
        start_dt = datetime.fromisoformat(registered) if registered else datetime.now()
    except Exception:
        start_dt = datetime.now()
    try:
        end_dt = datetime.fromisoformat(quality_at) if quality_at else datetime.now()
    except Exception:
        end_dt = datetime.now()
    waiting_minutes = max(0, int((end_dt - start_dt).total_seconds() / 60))
    repeated = conn.execute("""SELECT COALESCE(SUM(c-1),0) FROM (
        SELECT stage, COUNT(*) AS c FROM tracking_updates
        WHERE token=? AND stage!='In Transit' GROUP BY stage
    )""", (token,)).fetchone()[0] or 0
    unnecessary = max(0, visit_count - 1)
    score = max(0, min(100, round(100 - unnecessary*15 - min(45, waiting_minutes/30) - min(25, repeated*10))))
    return {
        "visit_count": visit_count,
        "unnecessary_visits": unnecessary,
        "waiting_minutes": waiting_minutes,
        "repeated_processes": int(repeated),
        "score": score,
        "first_registered_at": registered,
        "first_quality_at": quality_at
    }

@app.route("/api/effort/<token>")
@login_required
def effort_status(token):
    if not token_access_allowed(token):
        return jsonify({"error":"You can only view your own farmer records."}), 403
    token=token.strip().upper()
    conn=db()
    exists=conn.execute("SELECT 1 FROM farmers WHERE token=?",(token,)).fetchone()
    metrics=_effort_metrics(conn,token) if exists else None
    conn.close()
    if not metrics:
        return jsonify({"error":"Farmer token not found."}),404
    return jsonify(metrics)

@app.route("/api/effort/<token>/visit", methods=["POST"])
@admin_required
def effort_visit(token):
    token=token.strip().upper()
    conn=db()
    exists=conn.execute("SELECT 1 FROM farmers WHERE token=?",(token,)).fetchone()
    if not exists:
        conn.close(); return jsonify({"error":"Farmer token not found."}),404
    now=datetime.now().isoformat()
    conn.execute("UPDATE farmer_effort SET visit_count=visit_count+1,last_updated=? WHERE token=?",(now,token))
    conn.commit()
    metrics=_effort_metrics(conn,token)
    conn.close()
    return jsonify({"ok":True,**metrics})

LOT_STEPS=["farmer","quality","procurement","payment"]
@app.route("/api/lot-trace/<token>")
@login_required
def lot_trace_status(token):
    if not token_access_allowed(token):
        return jsonify({"error":"You can only view your own farmer records."}), 403
    token=token.strip().upper()
    conn=db()
    rows=conn.execute("""SELECT step_key,step_name,status,detail,updated_at
                         FROM lot_trace WHERE token=? ORDER BY id""",(token,)).fetchall()
    conn.close()
    if not rows:
        return jsonify({"error":"Lot trace not found."}),404
    return jsonify({"token":token,"trace":[{"step":r[0],"name":r[1],"status":r[2],"detail":r[3],"updated_at":r[4]} for r in rows]})

@app.route("/api/lot-trace/<token>/update", methods=["POST"])
@admin_required
def lot_trace_update(token):
    token=token.strip().upper()
    data=request.get_json(silent=True) or {}
    step=(data.get("step") or "").strip().lower()
    status=(data.get("status") or "Completed").strip()
    if step not in LOT_STEPS or status not in ("Pending","Completed","Rejected"):
        return jsonify({"error":"Invalid lot trace step or status."}),400
    conn=db()
    row=conn.execute("SELECT id,step_name FROM lot_trace WHERE token=? AND step_key=?",(token,step)).fetchone()
    if not row:
        conn.close(); return jsonify({"error":"Lot trace step not found."}),404

    # Enforce the real procurement order: farmer -> quality -> procurement -> payment.
    prerequisites={"quality":"farmer","procurement":"quality","payment":"procurement"}
    if status=="Completed" and step in prerequisites:
        prev=conn.execute("SELECT status FROM lot_trace WHERE token=? AND step_key=?",(token,prerequisites[step])).fetchone()
        if not prev or prev[0] != "Completed":
            conn.close(); return jsonify({"error":f"Complete the {prerequisites[step]} step before marking {step} completed."}),400
    now=datetime.now().isoformat()
    detail=(data.get("detail") or ("Step recorded by KisanGati" if status=="Completed" else "Step updated by KisanGati")).strip()
    conn.execute("UPDATE lot_trace SET status=?,detail=?,updated_at=? WHERE token=? AND step_key=?",(status,detail,now,token,step))
    if step=="quality" and status=="Completed":
        conn.execute("UPDATE farmer_effort SET first_quality_at=COALESCE(first_quality_at,?),last_updated=? WHERE token=?",(now,now,token))
    conn.commit()
    rows=conn.execute("SELECT step_key,step_name,status,detail,updated_at FROM lot_trace WHERE token=? ORDER BY id",(token,)).fetchall()
    conn.close()
    return jsonify({"ok":True,"trace":[{"step":r[0],"name":r[1],"status":r[2],"detail":r[3],"updated_at":r[4]} for r in rows]})

@app.route("/api/rejection/<token>", methods=["GET"])
@login_required
def rejection_list(token):
    if not token_access_allowed(token):
        return jsonify({"error":"You can only view your own farmer records."}), 403
    token=token.strip().upper()
    conn=db()
    rows=conn.execute("SELECT id,reason,guidance,created_at FROM rejection_records WHERE token=? ORDER BY id DESC",(token,)).fetchall()
    conn.close()
    return jsonify({"token":token,"rejections":[{"id":r[0],"reason":r[1],"guidance":r[2],"created_at":r[3]} for r in rows]})

@app.route("/api/rejection/<token>", methods=["POST"])
@admin_required
def rejection_save(token):
    token=token.strip().upper()
    data=request.get_json(silent=True) or {}
    reason=(data.get("reason") or "").strip()
    guidance=(data.get("guidance") or "").strip()
    if not reason or not guidance:
        return jsonify({"error":"Rejection reason and actionable guidance are required."}),400
    conn=db()
    exists=conn.execute("SELECT 1 FROM farmers WHERE token=?",(token,)).fetchone()
    if not exists:
        conn.close(); return jsonify({"error":"Farmer token not found."}),404
    now=datetime.now().isoformat()
    conn.execute("INSERT INTO rejection_records(token,reason,guidance,created_at) VALUES (?,?,?,?)",(token,reason,guidance,now))
    conn.execute("UPDATE lot_trace SET status='Rejected',detail=?,updated_at=? WHERE token=? AND step_key='quality'",(reason,now,token))
    conn.execute("UPDATE farmer_effort SET first_quality_at=COALESCE(first_quality_at,?),last_updated=? WHERE token=?",(now,now,token))
    conn.commit()
    conn.close()
    return jsonify({"ok":True,"message":"Rejection recorded successfully.","created_at":now})

@app.route("/api/admin/summary")
@admin_required
def admin_summary():
    conn=db()
    farmers=conn.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
    tracked=conn.execute("SELECT COUNT(*) FROM shipment_tracking").fetchone()[0]
    rejections=conn.execute("SELECT COUNT(*) FROM rejection_records").fetchone()[0]
    conn.close()
    return jsonify({"farmers":farmers,"tracked_lots":tracked,"rejections":rejections,"current_token":current_token})

@app.route("/api/queue")
def queue():
    global CURRENT_QUEUE_TOKEN
    current = CURRENT_QUEUE_TOKEN
    ahead = max(0, 104 - current - 1)
    return jsonify(current=f"P{current:03d}", ahead=ahead)

@app.route("/api/queue/next", methods=["POST"])
@admin_required
def queue_next():
    global CURRENT_QUEUE_TOKEN
    CURRENT_QUEUE_TOKEN = min(999, CURRENT_QUEUE_TOKEN + 1)
    return jsonify(current=f"P{CURRENT_QUEUE_TOKEN:03d}")

if __name__ == "__main__":
    db().close()
    print("KisanGati running at http://127.0.0.1:5000")
    app.run(debug=True)
