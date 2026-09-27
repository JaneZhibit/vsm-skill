import sys

file_path = r"d:\projects\HSM_msk_transport\frontend\src\routes\TripsHub.svelte"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Match the entire block starting from <!-- ==================== ... (PRO ...) ==================== -->
# to the end of its div wrapper.
pattern = re.compile(r'  <!-- ====================[^\n]+PRO[^\n]+==================== -->\n  <div class="mt-2 pt-4 border-t border-\[#2d2924\]">.*?  </div>\n  </div>', re.DOTALL)

replacement = """  <!-- ==================== СВОБОДНЫЙ ГОЛОСОВОЙ ТРЕНАЖЕР (PRO РЕЖИМ) ==================== -->
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
  </div>"""

new_content, count = pattern.subn(replacement, content)
if count > 0:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Success")
else:
    print("Pattern not found")
