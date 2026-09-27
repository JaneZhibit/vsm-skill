<script lang="ts">
  import { authStore } from '../lib/stores/authStore.svelte';
  import { trainWorld } from '../lib/stores/trainWorld.svelte';
  import { playClickSound, playSuccessSound, playErrorSound } from '../lib/utils/audio';

  // РђРєС‚РёРІРЅС‹Р№ РІС‹Р±СЂР°РЅРЅС‹Р№ РјРѕРґСѓР»СЊ (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ 'service')
  let selectedTrackId = $state<string>('service');

  interface Lesson {
    id: string;
    num: string;
    stationName: string;
    title: string;
    desc: string;
    status: 'completed' | 'unlocked' | 'locked';
    score?: number;
    reward: string;
    duration: string;
    km: string;
    incidentId: string;
  }

  interface Track {
    id: string;
    title: string;
    icon: string;
    lessons: Lesson[];
  }

  // Р§РµСЃС‚РЅР°СЏ РїСЂРѕРіСЂР°РјРјР° РѕР±СѓС‡РµРЅРёСЏ: 5 РјРѕРґСѓР»РµР№ Г— 3 СѓСЂРѕРєР° = 15 СѓСЂРѕРєРѕРІ
  // РЎС‚Р°С‚СѓСЃС‹ РІС‹СЃС‚Р°РІР»РµРЅС‹ СЂРѕРІРЅРѕ С‚Р°Рє, С‡С‚РѕР±С‹ РґР°РІР°С‚СЊ РІР°С€Рё 4/15 СЃРѕ СЃРєСЂРёРЅС€РѕС‚Р°!
  const modules: Track[] = [
    {
      id: 'service',
      title: 'Р‘Р°Р·РѕРІС‹Р№ СЃРµСЂРІРёСЃ',
      icon: 'рџЋ«',
      lessons: [
        {
          id: 'lesson_service_1',
          num: '1.1',
          stationName: 'СЃС‚. Р РёР¶СЃРєР°СЏ',
          title: 'РЎР°РјРѕРІРѕР»СЊРЅР°СЏ РїРµСЂРµСЃР°РґРєР°',
          desc: 'РџР°СЃСЃР°Р¶РёСЂ Р±РµР· РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РїРµСЂРµСЃРµР» РЅР° С‡СѓР¶РѕРµ РјРµСЃС‚Рѕ Сѓ РѕРєРЅР° Рё РЅРµ Р¶РµР»Р°РµС‚ РІРѕР·РІСЂР°С‰Р°С‚СЊСЃСЏ.',
          status: 'completed',
          score: 100,
          reward: '+25 Р РµРіР»Р°РјРµРЅС‚',
          duration: '2 РјРёРЅ',
          km: '5 РєРј',
          incidentId: 'inc_wrong_seat_01',
        },
        {
          id: 'lesson_service_2',
          num: '1.2',
          stationName: 'СЃС‚. Р—РµР»РµРЅРѕРіСЂР°Рґ',
          title: 'Р§РµРјРѕРґР°РЅ РІ РїСЂРѕС…РѕРґРµ',
          desc: 'РџР°СЃСЃР°Р¶РёСЂ Р·Р°Р±Р»РѕРєРёСЂРѕРІР°Р» С†РµРЅС‚СЂР°Р»СЊРЅС‹Р№ СЌРІР°РєСѓР°С†РёРѕРЅРЅС‹Р№ РїСЂРѕС…РѕРґ С‚СЏР¶РµР»С‹Рј С‡РµРјРѕРґР°РЅРѕРј.',
          status: 'completed',
          score: 95,
          reward: '+25 Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ',
          duration: '2 РјРёРЅ',
          km: '41 РєРј',
          incidentId: 'inc_luggage_aisle_01',
        },
        {
          id: 'lesson_service_3',
          num: '1.3',
          stationName: 'СЃС‚. РўРІРµСЂСЊ',
          title: 'РџРѕСЃР°РґРѕС‡РЅС‹Р№ СЌРєСЃРїСЂРµСЃСЃ',
          desc: 'РћС‚СЂР°Р±РѕС‚РєР° РєРѕРјРїР»РµРєСЃРЅРѕРіРѕ РїРѕСЃР»РµРїРѕСЃР°РґРѕС‡РЅРѕРіРѕ РѕР±С…РѕРґР° Рё СЃРІРµСЂРєРё Р·Р°РЅСЏС‚РѕСЃС‚Рё РєСЂРµСЃРµР».',
          status: 'unlocked',
          reward: '+30 РЎРµСЂРІРёСЃ',
          duration: '3 РјРёРЅ',
          km: '167 РєРј',
          incidentId: 'inc_wrong_seat_01',
        },
      ],
    },
    {
      id: 'comfort',
      title: 'РњРёРєСЂРѕРєР»РёРјР°С‚ Рё Р±С‹С‚',
      icon: 'рџЊЎпёЏ',
      lessons: [
        {
          id: 'lesson_comfort_1',
          num: '2.1',
          stationName: 'СЃС‚. Р’С‹СЃРѕРєРѕРІРѕ',
          title: 'РЎРєРІРѕР·РЅСЏРє РѕС‚ РєРѕРЅРґРёС†РёРѕРЅРµСЂР°',
          desc: 'Р–Р°Р»РѕР±Р° РЅР° С…РѕР»РѕРґРЅС‹Р№ РѕР±РґСѓРІ Рё С‚СЂРµР±РѕРІР°РЅРёРµ РїР°СЃСЃР°Р¶РёСЂР° РѕС‚РєСЂС‹С‚СЊ РіР»СѓС…РѕРµ РѕРєРЅРѕ РЅР° 400 РєРј/С‡.',
          status: 'completed',
          score: 90,
          reward: '+20 РљРѕРјС„РѕСЂС‚',
          duration: '2 РјРёРЅ',
          km: '86 РєРј',
          incidentId: 'inc_temp_01',
        },
        {
          id: 'lesson_comfort_2',
          num: '2.2',
          stationName: 'СЃС‚. РќРѕРІР°СЏ РўРІРµСЂСЊ',
          title: 'Р РѕР·РµС‚РєР° РїРѕРґ РєСЂРµСЃР»РѕРј',
          desc: 'РќРµ РїРѕРґР°РµС‚СЃСЏ РїРёС‚Р°РЅРёРµ 220V РЅР° Р±Р»РѕРє Р·Р°СЂСЏРґРєРё Сѓ РєСЂРµСЃР»Р° РїРµСЂРІРѕРіРѕ РєР»Р°СЃСЃР°. РќРѕСѓС‚Р±СѓРє СЃР°РґРёС‚СЃСЏ.',
          status: 'unlocked',
          reward: '+25 РЎРµСЂРІРёСЃ',
          duration: '2 РјРёРЅ',
          km: '167 РєРј',
          incidentId: 'inc_broken_socket_01',
        },
        {
          id: 'lesson_comfort_3',
          num: '2.3',
          stationName: 'СЃС‚. РўРѕСЂР¶РѕРє',
          title: 'РЎРµСЂРІРёСЃ СЂР°С†РёРѕРЅР° Р±РёСЃС‚СЂРѕ',
          desc: 'Р—Р°РєРѕРЅС‡РёР»РѕСЃСЊ Р±Р»СЋРґРѕ РёР· РјРµРЅСЋ, РїР°СЃСЃР°Р¶РёСЂ С‚СЂРµР±СѓРµС‚ РІС‹Р·РІР°С‚СЊ С€РµС„-РїРѕРІР°СЂР° Рё РЅР°С‡Р°Р»СЊРЅРёРєР° РїРѕРµР·РґР°.',
          status: 'locked',
          reward: '+25 РЎРµСЂРІРёСЃ',
          duration: '3 РјРёРЅ',
          km: '225 РєРј',
          incidentId: 'inc_temp_01',
        },
      ],
    },
    {
      id: 'safety',
      title: 'Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ',
      icon: 'рџ›ЎпёЏ',
      lessons: [
        {
          id: 'lesson_safety_1',
          num: '3.1',
          stationName: 'СЃС‚. РЎР°РґРІР°',
          title: 'Р’РµР№Рї РІ СЃР°Р»РѕРЅРµ РІР°РіРѕРЅР°',
          desc: 'РљСѓСЂРµРЅРёРµ РёСЃРїР°СЂРёС‚РµР»СЏ В«РІ РєСѓР»Р°РєВ» Рё РїСЂСЏРјР°СЏ СѓРіСЂРѕР·Р° Р»РѕР¶РЅРѕРіРѕ СЃСЂР°Р±Р°С‚С‹РІР°РЅРёСЏ РґР°С‚С‡РёРєРѕРІ РґС‹РјР°.',
          status: 'unlocked',
          reward: '+35 Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ',
          duration: '2 РјРёРЅ',
          km: '280 РєРј',
          incidentId: 'inc_vape_smoke_01',
        },
        {
          id: 'lesson_safety_2',
          num: '3.2',
          stationName: 'СЃС‚. Р‘РѕР»РѕРіРѕРµ',
          title: 'Р‘РµСЃС…РѕР·РЅС‹Р№ СЂСЋРєР·Р°Рє',
          desc: 'РћР±РЅР°СЂСѓР¶РµРЅРёРµ Р·Р°Р±С‹С‚РѕР№ РїРѕРґРѕР·СЂРёС‚РµР»СЊРЅРѕР№ СЃСѓРјРєРё СЃ РїСЂРѕРІРѕРґР°РјРё РїРѕРґ РєСЂРµСЃР»РѕРј РІ РїСЂРѕС…РѕРґРµ.',
          status: 'locked',
          reward: '+40 Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ',
          duration: '2.5 РјРёРЅ',
          km: '330 РєРј',
          incidentId: 'inc_unclaimed_bag_01',
        },
        {
          id: 'lesson_safety_3',
          num: '3.3',
          stationName: 'СЃС‚. Р’Р°Р»РґР°Р№',
          title: 'РђРІР°СЂРёР№РЅС‹Рµ РїСЂРѕС‚РѕРєРѕР»С‹',
          desc: 'Р”РµР№СЃС‚РІРёСЏ РїРѕРµР·РґРЅРѕР№ Р±СЂРёРіР°РґС‹ РїСЂРё РїР°РґРµРЅРёРё РґР°РІР»РµРЅРёСЏ РІ РјР°РіРёСЃС‚СЂР°Р»Рё Рё Р°РІР°СЂРёР№РЅРѕРј С‚РѕСЂРјРѕР¶РµРЅРёРё.',
          status: 'locked',
          reward: '+50 Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ',
          duration: '3 РјРёРЅ',
          km: '398 РєРј',
          incidentId: 'inc_unclaimed_bag_01',
        },
      ],
    },
    {
      id: 'conflicts',
      title: 'РљРѕРЅС„Р»РёРєС‚РѕР»РѕРіРёСЏ',
      icon: 'рџ—ЈпёЏ',
      lessons: [
        {
          id: 'lesson_conflicts_1',
          num: '4.1',
          stationName: 'СЃС‚. Р’РµР»РёРєРёР№ РќРѕРІРіРѕСЂРѕРґ',
          title: 'Р—РІРѕРЅРѕРє РЅР° РІРµСЃСЊ СЃР°Р»РѕРЅ',
          desc: 'Р‘РёР·РЅРµСЃ-РїР°СЃСЃР°Р¶РёСЂ РІРµРґРµС‚ РіСЂРѕРјРєРёРµ РїРµСЂРµРіРѕРІРѕСЂС‹ РїРѕ РіСЂРѕРјРєРѕР№ СЃРІСЏР·Рё Рё С…Р°РјРёС‚ СЃРѕСЃРµРґСЏРј.',
          status: 'completed',
          score: 88,
          reward: '+20 Р­С‚РёРєР°',
          duration: '2 РјРёРЅ',
          km: '530 РєРј',
          incidentId: 'inc_noise_business_01',
        },
        {
          id: 'lesson_conflicts_2',
          num: '4.2',
          stationName: 'СЃС‚. Р–Р°СЂРѕРІСЃРєР°СЏ',
          title: 'РќРµС‚СЂРµР·РІС‹Р№ РґРµР±РѕС€РёСЂ',
          desc: 'РџР°СЃСЃР°Р¶РёСЂ С‚СЂРµР±СѓРµС‚ РєРѕРЅСЊСЏРє Рё СѓРіСЂРѕР¶Р°РµС‚ СѓРІРѕР»СЊРЅРµРЅРёРµРј. РџСЂР°РІРёР»Р° СЂР°РґРёРѕРїРµСЂРµРіРѕРІРѕСЂРѕРІ СЃ Р›РќРџ.',
          status: 'unlocked',
          reward: '+30 Р РµРіР»Р°РјРµРЅС‚',
          duration: '2.5 РјРёРЅ',
          km: '630 РєРј',
          incidentId: 'inc_drunk_conflict_01',
        },
        {
          id: 'lesson_conflicts_3',
          num: '4.3',
          stationName: 'СЃС‚. РћР±СѓС…РѕРІРѕ',
          title: 'РЎСЉРµРјРєР° РЅР° С‚РµР»РµС„РѕРЅ',
          desc: 'Р‘Р»РѕРіРµСЂ РЅР°РІСЏР·С‡РёРІРѕ СЃРЅРёРјР°РµС‚ Р»РёС†Р° РїРѕРїСѓС‚С‡РёРєРѕРІ СЃРѕ С€С‚Р°С‚РёРІР° Р±РµР· РёС… СЃРѕРіР»Р°СЃРёСЏ (152-Р¤Р—).',
          status: 'locked',
          reward: '+30 Р­С‚РёРєР°',
          duration: '2 РјРёРЅ',
          km: '668 РєРј',
          incidentId: 'inc_noise_business_01',
        },
      ],
    },
    {
      id: 'medicine',
      title: 'Р”РѕРІСЂР°С‡РµР±РЅР°СЏ РїРѕРјРѕС‰СЊ',
      icon: 'рџ©є',
      lessons: [
        {
          id: 'lesson_medicine_1',
          num: '5.1',
          stationName: 'СЃС‚. Р›РѕРіРѕРІРµР¶СЊ',
          title: 'РљРёРЅРµС‚РѕР· РЅР° 380 РєРј/С‡',
          desc: 'РЈРєР°С‡РёРІР°РЅРёРµ Рё С‚РѕС€РЅРѕС‚Р° РЅР° СЃРєРѕСЂРѕСЃС‚РЅРѕР№ РґСѓРіРµ РїСЂРё РґРІРёР¶РµРЅРёРё РїСЂРѕС‚РёРІ С…РѕРґР° РїРѕРµР·РґР°.',
          status: 'unlocked',
          reward: '+25 РњРµРґРёС†РёРЅР°',
          duration: '2 РјРёРЅ',
          km: '225 РєРј',
          incidentId: 'inc_kinetosis_01',
        },
        {
          id: 'lesson_medicine_2',
          num: '5.2',
          stationName: 'СЃС‚. РўРёРіРѕРґР°',
          title: 'РўР°Р±Р»РµС‚РєР° РёР· СЃСѓРјРѕС‡РєРё',
          desc: 'РџСЂРѕСЃСЊР±Р° РґР°С‚СЊ Р»РёС‡РЅС‹Р№ Р°РЅР°Р»СЊРіРёРЅ РёР»Рё РЅСѓСЂРѕС„РµРЅ. РљР°С‚РµРіРѕСЂРёС‡РµСЃРєРёР№ Р·Р°РїСЂРµС‚ РїРѕ РЎРўРћ Р Р–Р”.',
          status: 'locked',
          reward: '+35 РњРµРґРёС†РёРЅР°',
          duration: '2 РјРёРЅ',
          km: '590 РєРј',
          incidentId: 'inc_med_pills_01',
        },
        {
          id: 'lesson_medicine_3',
          num: '5.3',
          stationName: 'СЃС‚. РЎРџР± Р“Р»Р°РІРЅС‹Р№',
          title: 'РџР°РЅРёС‡РµСЃРєР°СЏ Р°С‚Р°РєР°',
          desc: 'РћСЃС‚СЂР°СЏ РіРёРїРµСЂРІРµРЅС‚РёР»СЏС†РёСЏ Рё СЃС‚СЂР°С… СЃРєРѕСЂРѕСЃС‚Рё. РўРµС…РЅРёРєР° РґС‹С…Р°РЅРёСЏ РїРѕ РєРІР°РґСЂР°С‚Сѓ Рё СЌРјРїР°С‚РёСЏ.',
          status: 'locked',
          reward: '+40 РњРµРґРёС†РёРЅР°',
          duration: '3 РјРёРЅ',
          km: '679 РєРј',
          incidentId: 'inc_kinetosis_01',
        },
      ],
    },
  ];

  // РђРєС‚РёРІРЅС‹Р№ РІС‹Р±СЂР°РЅРЅС‹Р№ С‚СЂРµРє
  const activeTrack = $derived(modules.find((m) => m.id === selectedTrackId) || modules[0]);

  // РџРѕРґСЃС‡РµС‚ РѕР±С‰РµРіРѕ РїСЂРѕРіСЂРµСЃСЃР°
  const totalCompleted = $derived(
    modules.reduce((acc, m) => acc + m.lessons.filter((l) => l.status === 'completed').length, 0)
  );
  const totalLessons = 15;

  const rank = $derived(
    totalCompleted < 4
      ? 'рџЋ“ РЎС‚Р°Р¶РµСЂ'
      : totalCompleted < 9
        ? 'рџҐ‰ РњР»Р°РґС€РёР№ РїСЂРѕРІРѕРґРЅРёРє'
        : totalCompleted < 13
          ? 'рџҐ€ РџСЂРѕРІРѕРґРЅРёРє Р±РёР·РЅРµСЃ-РєР»Р°СЃСЃР°'
          : 'рџҐ‡ РЎС‚Р°СЂС€РёР№ РїСЂРѕРІРѕРґРЅРёРє'
  );

  const examUnlocked = true; // РћС‚РєСЂС‹С‚ РґР»СЏ РёРЅС‚РµСЂР°РєС‚РёРІРЅРѕРіРѕ РіРѕР»РѕСЃРѕРІРѕРіРѕ С‚РµСЃС‚РёСЂРѕРІР°РЅРёСЏ РЅР° Р·Р°С‰РёС‚Рµ
  const progressPercent = $derived(Math.round((totalCompleted / totalLessons) * 100));

  function selectTrack(trackId: string) {
    playClickSound();
    selectedTrackId = trackId;
  }

  async function startLesson(lesson: Lesson) {
    if (lesson.status === 'locked') {
      playErrorSound();
      return;
    }
    playSuccessSound();
    // Р—Р°РїСѓСЃРєР°РµРј РїРµСЂСЃРѕРЅР°Р»СЊРЅС‹Р№ СѓСЂРѕРє С‡РµСЂРµР· API Р±СЌРєРµРЅРґР°
    await trainWorld.startNewTrip(lesson.id);
    authStore.setRoute('simulator');
  }

  async function startVoiceExam() {
    playSuccessSound();
    // РРЎРџР РђР’Р›Р•РќРћ: РўРµРїРµСЂСЊ РјС‹ РїРµСЂРµРґР°РµРј 'pro', С‡С‚РѕР±С‹ РІРєР»СЋС‡РёС‚СЊ РЅСѓР¶РЅС‹Р№ UI СЃ РјРёРєСЂРѕС„РѕРЅРѕРј!
    await trainWorld.startNewTrip('pro');
    authStore.setRoute('simulator');
  }
</script>

<div class="w-full max-w-5xl mx-auto p-4 sm:p-6 pb-40 md:pb-8 flex flex-col gap-6 selection:bg-amber-500 selection:text-black">
  <!-- ==================== РЁРђРџРљРђ РђРљРђР”Р•РњРР ==================== -->
  <header class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2d2924] pb-4">
    <div>
      <h1 class="text-lg sm:text-xl font-bold text-[#f5f3ef] tracking-wide flex items-center gap-2">
        <span>РђРєР°РґРµРјРёСЏ РїСЂРѕРІРѕРґРЅРёРєРѕРІ Р’РЎРњ</span>
        <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
          РЎРљРћР РћРЎРўР¬ Р”Рћ 400 РљРњ/Р§
        </span>
      </h1>
      <p class="text-xs text-[#a39e95] mt-0.5">
        РџСЂРѕР№РґРёС‚Рµ С‚РµРјР°С‚РёС‡РµСЃРєРёРµ СЃС‚Р°РЅС†РёРё-СѓСЂРѕРєРё РЅР° СЃРєРѕСЂРѕСЃС‚РЅРѕР№ РјР°РіРёСЃС‚СЂР°Р»Рё В«Р‘РµР»С‹Р№ РєСЂРµС‡РµС‚В»
      </p>
    </div>

    <!-- РРЅРґРёРєР°С‚РѕСЂ РїСЂРѕРіСЂРµСЃСЃР° Рё С‚РµРєСѓС‰РµРіРѕ СЂР°РЅРіР° (СЃРѕ СЃРєСЂРёРЅС€РѕС‚Р°) -->
    <div class="flex flex-col items-end gap-1.5 shrink-0">
      <div class="text-sm font-bold text-amber-400 flex items-center gap-1.5">
        <span>{rank}</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-32 h-2 bg-[#282420] rounded-full overflow-hidden border border-[#3d3831]">
          <div
            class="h-full bg-gradient-to-r from-amber-600 to-yellow-400 rounded-full transition-all duration-500"
            style="width: {progressPercent}%;"
          ></div>
        </div>
        <span class="text-[11px] text-[#a39e95] font-mono font-bold">
          {totalCompleted}/{totalLessons}
        </span>
      </div>
    </div>
  </header>

  <!-- ==================== Р’Р•Р РҐРќРР™ Р РЇР”: РўРђР‘Р« РњРћР”РЈР›Р•Р™ ==================== -->
  <div class="flex flex-col gap-2">
    <div class="text-[11px] font-bold text-[#a39e95] uppercase tracking-wider">
      Р’С‹Р±РµСЂРёС‚Рµ РЅР°РїСЂР°РІР»РµРЅРёРµ РїРѕРґРіРѕС‚РѕРІРєРё:
    </div>

    <!-- Р“РѕСЂРёР·РѕРЅС‚Р°Р»СЊРЅР°СЏ Р»РёРЅРµР№РєР° 5 РјРѕРґСѓР»РµР№ -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
      {#each modules as mod}
        {@const completedCount = mod.lessons.filter((l) => l.status === 'completed').length}
        {@const isSelected = selectedTrackId === mod.id}
        <button
          onclick={() => selectTrack(mod.id)}
          class="p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-2 relative overflow-hidden group {isSelected
            ? 'bg-amber-950/40 border-amber-500/80 shadow-[0_0_15px_rgba(245,158,11,0.2)]'
            : 'bg-[#141210]/80 border-[#2d2924] hover:border-[#3d3831] hover:bg-[#1a1816]'}"
        >
          <!-- РђРєС‚РёРІРЅР°СЏ РїРѕР»РѕСЃР° СЃРЅРёР·Сѓ -->
          {#if isSelected}
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 to-yellow-400"></div>
          {/if}

          <div class="flex items-center justify-between">
            <span class="text-xl group-hover:scale-110 transition-transform">{mod.icon}</span>
            <span
              class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded {completedCount === 3
                ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-600/40'
                : 'bg-[#282420] text-amber-300 border border-[#3d3831]'}"
            >
              {completedCount}/3
            </span>
          </div>

          <div>
            <div class="text-xs font-bold truncate {isSelected ? 'text-amber-300' : 'text-[#f5f3ef]'}">
              {mod.title}
            </div>
            <div class="w-full h-1 bg-[#282420] rounded-full overflow-hidden mt-1.5">
              <div
                class="h-full bg-amber-500 rounded-full"
                style="width: {(completedCount / 3) * 100}%;"
              ></div>
            </div>
          </div>
        </button>
      {/each}
    </div>
  </div>

  <!-- ==================== РЎР•РљР¦РРЇ: Р–Р•Р›Р•Р—РќРћР”РћР РћР–РќР«Р™ РџРЈРўР¬ Р РљРђР РўРћР§РљР-Р’РђР“РћРќР« ==================== -->
  <div class="flex flex-col gap-3 mt-2">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm">рџљ„</span>
        <h2 class="text-xs sm:text-sm font-bold text-[#f5f3ef] uppercase tracking-wider">
          Р›РёРЅРёСЏ РїРµСЂРµРіРѕРЅРѕРІ: {activeTrack.title}
        </h2>
      </div>
      <span class="text-[11px] text-[#706b63] font-mono hidden sm:inline">
        РЎРєСЂРѕР»Р»РёСЂСѓР№С‚Рµ СЃС‚Р°РЅС†РёРё СЃР»РµРІР° РЅР°РїСЂР°РІРѕ вћ”
      </span>
    </div>

    <!-- РљРѕРЅС‚РµР№РЅРµСЂ СЂРµР»СЊСЃРѕРІРѕРіРѕ РїРѕР»РѕС‚РЅР° СЃРѕ С€РїР°Р»Р°РјРё -->
    <div class="railway-track-wrapper p-4 sm:p-6 rounded-2xl bg-[#141210]/90 border border-[#2d2924] relative overflow-hidden">
      <!-- РњРµС‚Р°Р»Р»РёС‡РµСЃРєР°СЏ РєРѕР»РµСЏ СЃРѕ С€РїР°Р»Р°РјРё РЅР° С„РѕРЅРµ -->
      <div class="rail-ties-bg"></div>
      <div class="rail-line-top"></div>
      <div class="rail-line-bottom"></div>

      <!-- Р“РѕСЂРёР·РѕРЅС‚Р°Р»СЊРЅР°СЏ РєР°СЂСѓСЃРµР»СЊ РєР°СЂС‚РѕС‡РµРє (СЂСѓР»РµС‚РєР° СѓСЂРѕРєРѕРІ) -->
      <div class="flex gap-4 sm:gap-6 overflow-x-auto pb-2 pt-1 snap-x snap-mandatory relative z-10 hide-scrollbar">
        {#each activeTrack.lessons as lesson}
          <!-- РљР°СЂС‚РѕС‡РєР°-РІР°РіРѕРЅ (РЎС‚Р°РЅС†РёСЏ РјР°СЂС€СЂСѓС‚Р°) -->
          <div
            class="snap-center min-w-[280px] sm:min-w-[310px] max-w-[320px] rounded-2xl border p-4 sm:p-5 flex flex-col justify-between gap-4 transition-all duration-200 relative group {lesson.status ===
            'completed'
              ? 'bg-[#1a1816] border-emerald-600/40 shadow-md shadow-emerald-950/20'
              : lesson.status === 'unlocked'
                ? 'bg-gradient-to-b from-[#1f1b16] to-[#141210] border-amber-500/80 shadow-[0_0_25px_rgba(245,158,11,0.25)]'
                : 'bg-[#12110f]/80 border-[#262320] opacity-60'}"
          >
            <!-- РЎС‚Р°РЅС†РёРѕРЅРЅС‹Р№ С€С‚Р°РјРї / Р§РµРєРїРѕРёРЅС‚ -->
            <div>
              <div class="flex items-center justify-between gap-2 mb-3">
                <span
                  class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full flex items-center gap-1 {lesson.status ===
                  'completed'
                    ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-500/40'
                    : lesson.status === 'unlocked'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
                      : 'bg-[#282420] text-[#706b63] border border-[#3d3831]'}"
                >
                  {#if lesson.status === 'completed'}
                    <span>вњ“</span> <span>РџР РћР™Р”Р•РќРћ</span>
                  {:else if lesson.status === 'unlocked'}
                    <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> <span>Р”РћРЎРўРЈРџРќРћ</span>
                  {:else}
                    <span>рџ”’</span> <span>Р—РђРљР Р«РўРћ</span>
                  {/if}
                </span>

                <span class="text-[10px] text-[#a39e95] font-mono">
                  {lesson.km} вЂў {lesson.duration}
                </span>
              </div>

              <!-- РќР°Р·РІР°РЅРёРµ Рё СЃС‚Р°РЅС†РёСЏ -->
              <div class="text-[10px] text-amber-400/90 font-mono uppercase font-bold tracking-wider mb-0.5">
                {lesson.stationName} вЂў РЈСЂРѕРє {lesson.num}
              </div>
              <h3 class="text-sm sm:text-base font-bold text-[#f5f3ef] mb-2 leading-snug">
                {lesson.title}
              </h3>
              <p class="text-xs text-[#a39e95] leading-relaxed line-clamp-2">
                {lesson.desc}
              </p>
            </div>

            <!-- РќРёР¶РЅСЏСЏ РїР»Р°С€РєР°: РќР°РіСЂР°РґР° Рё РљРЅРѕРїРєР° СЃС‚Р°СЂС‚Р° -->
            <div class="pt-3 border-t border-[#2d2924] flex flex-col gap-2.5">
              <div class="flex items-center justify-between text-[11px] font-mono">
                <span class="text-[#706b63]">РќР°РіСЂР°РґР° Р—РЈРќ:</span>
                <span class="font-bold text-amber-300">{lesson.reward}</span>
              </div>

              {#if lesson.status === 'completed'}
                <button
                  onclick={() => startLesson(lesson)}
                  class="w-full py-2.5 px-4 rounded-xl bg-[#282420] hover:bg-[#342f2a] border border-[#3d3831] hover:border-amber-400/60 text-xs font-bold text-[#f5f3ef] transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <span>РџРѕРІС‚РѕСЂРёС‚СЊ (РЎ РїРѕРґСЃРєР°Р·РєР°РјРё)</span>
                  <span class="text-amber-400">в†є</span>
                </button>
              {:else if lesson.status === 'unlocked'}
                <button
                  onclick={() => startLesson(lesson)}
                  class="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-stone-950 text-xs font-bold tracking-wide shadow-md shadow-amber-500/25 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer flex items-center justify-center gap-2"
                >
                  <span>рџЋ™пёЏ Р“РѕР»РѕСЃРѕРІРѕР№ СЂРµР№СЃ (РЎ РїРѕРґСЃРєР°Р·РєР°РјРё)</span>
                </button>
              {:else}
                <button
                  disabled
                  class="w-full py-2.5 px-4 rounded-xl bg-[#1c1a17] border border-[#2d2924] text-xs font-semibold text-[#5c5750] cursor-not-allowed flex items-center justify-center gap-1.5"
                >
                  <span>РќРµРґРѕСЃС‚СѓРїРЅРѕ</span>
                  <span>рџ”’</span>
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- ==================== СВОБОДНЫЙ ГОЛОСОВОЙ ТРЕНАЖЕР (PRO РЕЖИМ) ==================== -->
  <div class="mt-2 pt-4 border-t border-[#2d2924]">
    <div class="text-[11px] font-bold text-amber-500 uppercase tracking-wider mb-3 flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
      Свободный режим (Динамическая генерация инцидентов)
    </div>

    <div class="p-5 sm:p-6 rounded-2xl border flex flex-col md:flex-row items-center justify-between gap-5 relative overflow-hidden bg-gradient-to-r from-[#2a1708] to-[#140b04] border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.15)]">

      <div class="flex-1 space-y-2 relative z-10">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-2xl">🎙️</span>
          <h2 class="text-sm sm:text-base font-bold text-amber-400 uppercase tracking-wider">
            PRO-Рейс: Голосовой тренажер
          </h2>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            С ИИ-подсказками
          </span>
        </div>
        <p class="text-xs text-[#a39e95] leading-relaxed max-w-2xl">
          Сценарий будет сгенерирован ИИ-директором на основе ваших слабых зон ЗУН. Инциденты решаются голосом, <strong class="text-emerald-400">система будет давать вам подсказки</strong> по регламенту. Пассажиры (ИИ) будут отвечать вам в реальном времени. Будьте вежливы!
        </p>
      </div>

      <button
        onclick={startVoiceExam}
        class="relative z-10 shrink-0 px-6 py-3.5 rounded-xl font-bold text-xs sm:text-sm transition-all flex items-center gap-2 bg-gradient-to-r from-rose-600 via-orange-600 to-amber-500 hover:scale-105 text-white shadow-lg shadow-rose-500/30 cursor-pointer border border-rose-400/50"
      >
        <span>🔥 Запустить PRO-рейс ➔</span>
      </button>
    </div>
  </div>
</div>

<style>
  /* Р–РµР»РµР·РЅРѕРґРѕСЂРѕР¶РЅРѕРµ РїРѕР»РѕС‚РЅРѕ Р’РЎРњ: СЂРµР»СЊСЃС‹ Рё С€РїР°Р»С‹ */
  .railway-track-wrapper {
    position: relative;
  }

  /* РЁРїР°Р»С‹ (РїРѕРІС‚РѕСЂСЏСЋС‰РёРµСЃСЏ С€С‚СЂРёС…Рё) */
  .rail-ties-bg {
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    height: 48px;
    background-image: repeating-linear-gradient(
      90deg,
      rgba(61, 56, 49, 0.45) 0px,
      rgba(61, 56, 49, 0.45) 5px,
      transparent 5px,
      transparent 28px
    );
    pointer-events: none;
    z-index: 1;
  }

  /* Р’РµСЂС…РЅРёР№ СЂРµР»СЊСЃ */
  .rail-line-top {
    position: absolute;
    left: 0;
    right: 0;
    top: calc(50% - 16px);
    height: 2px;
    background: linear-gradient(90deg, #3d3831, rgba(245, 158, 11, 0.6), #3d3831);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.3);
    pointer-events: none;
    z-index: 2;
  }

  /* РќРёР¶РЅРёР№ СЂРµР»СЊСЃ */
  .rail-line-bottom {
    position: absolute;
    left: 0;
    right: 0;
    top: calc(50% + 16px);
    height: 2px;
    background: linear-gradient(90deg, #3d3831, rgba(245, 158, 11, 0.6), #3d3831);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.3);
    pointer-events: none;
    z-index: 2;
  }

  /* РЎРєСЂС‹С‚РёРµ РїРѕР»РѕСЃС‹ РїСЂРѕРєСЂСѓС‚РєРё РґР»СЏ СЂСѓР»РµС‚РєРё */
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
</style>
