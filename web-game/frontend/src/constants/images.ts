// Image constants for the Arise web game
export const IMAGES = {
  // Character portraits
  CHARACTERS: {
    ALICIA_BLANCHE: '/images/alicia_blanche.png',
    AMAMIYA_MIREI: '/images/amamiya_mirei.png',
    ANNA_RUIZ: '/images/anna_ruiz.png',
    BAEK_YOONHO: '/images/baek_yoonho.png',
    CARL: '/images/carl.png',
    CHA_HAE_IN: '/images/cha_hae-in.png',
    CHARLOTTE: '/images/charlotte.png',
    CHOI_JONG_IN: '/images/choi_jong-in.png',
    CID_KAGENOU: '/images/cid_kagenou.png',
    EMMA_LAURENT: '/images/emma__laurent.png',
    ESIL_RADIRU: '/images/esil_radiru.png',
    GINA: '/images/gina.png',
    GO_GUNHEE: '/images/go_gunhee.png',
    GOTO_RYUJI: '/images/goto_ryuji.png',
    HAN_SE_MI: '/images/han_se-mi.png',
    HAN_SONG_YI: '/images/han_song-yi.png',
    HARPER: '/images/harper.png',
    HWANG_DONGSOO: '/images/hwang_dongsoo.png',
    HWANG_DONGSUK: '/images/hwang_dongsuk.png',
    ISLA_WRIGHT: '/images/isla_wright.png',
    JO_KYUHWAN: '/images/jo_kyuhwan.png',
    KANG_TAESHIK: '/images/kang_taeshik.png',
    KIM_CHUL: '/images/kim_chul.png',
    KIM_SANGSHIK: '/images/kim_sangshik.png',
    KIRITSUGU_EMIYA: '/images/kiritsugu_emiya.png',
    LEE_BORA: '/images/lee_bora.png',
    LEE_JOOHEE: '/images/lee_joohee.png',
    LIM_TAE_GYU: '/images/lim_tae-gyu.png',
    MEILIN_FISHER: '/images/meilin_fisher.png',
    MELIODAS: '/images/meliodas.png',
    MIN_BYUNG_GU: '/images/min_byung-gu.png',
    NAM_CHAE_YOUNG: '/images/nam_chae-young.png',
    PARK_BEOM_SHIK: '/images/park_beom-shik.png',
    PARK_HEEJIN: '/images/park_heejin.png',
    PORTGAS_D_ACE: '/images/portgas_d._ace.png',
    RYOMEN_SUKUNA: '/images/ryomen_sukuna.png',
    SATELLA: '/images/satella.png',
    SEO_JIWOO: '/images/seo_jiwoo.png',
    SEORIN: '/images/seorin.png',
    SHIMIZU_AKARI: '/images/shimizu_akari.png',
    SILVER_MANE_BAEK_YOONHO: '/images/silver_mane_baek_yoonho.png',
    SONG_CHIYUL: '/images/song_chiyul.png',
    TANYA_DEGURECHAFF: '/images/tanya_degurechaff.png',
    TAWATA_KANAE: '/images/tawata_kanae.png',
    THOMAS_ANDRE: '/images/thomas_andre.png',
    WICK: '/images/wick.png',
    WOO_JINCHUL: '/images/woo_jinchul.png',
    YOO_JINHO: '/images/yoo_jinho.png',
    YOO_SOOHYUN: '/images/yoo_soohyun.png',
  },

  // Profile and special images
  PROFILES: {
    DEFAULT_PROFILE: '/images/profile.png',
    THOMAS_1: '/images/thomas.png',
    THOMAS_2: '/images/thomas (1).png',
  },

  // Character arrays for random selection
  RANDOM_CHARACTERS: [
    '/images/alicia_blanche.png',
    '/images/amamiya_mirei.png',
    '/images/anna_ruiz.png',
    '/images/baek_yoonho.png',
    '/images/cha_hae-in.png',
    '/images/charlotte.png',
    '/images/choi_jong-in.png',
    '/images/esil_radiru.png',
    '/images/goto_ryuji.png',
    '/images/han_se-mi.png',
    '/images/lee_joohee.png',
    '/images/meilin_fisher.png',
    '/images/park_heejin.png',
    '/images/seorin.png',
    '/images/shimizu_akari.png',
    '/images/tawata_kanae.png',
  ],

  // Boss/Enemy characters
  BOSSES: [
    '/images/ryomen_sukuna.png',
    '/images/meliodas.png',
    '/images/thomas_andre.png',
    '/images/hwang_dongsoo.png',
    '/images/kang_taeshik.png',
    '/images/cid_kagenou.png',
  ],

  // Hero characters
  HEROES: [
    '/images/cha_hae-in.png',
    '/images/baek_yoonho.png',
    '/images/choi_jong-in.png',
    '/images/goto_ryuji.png',
    '/images/woo_jinchul.png',
    '/images/go_gunhee.png',
  ],
};

// Helper functions
export const getRandomCharacter = (): string => {
  const characters = IMAGES.RANDOM_CHARACTERS;
  return characters[Math.floor(Math.random() * characters.length)];
};

export const getRandomBoss = (): string => {
  const bosses = IMAGES.BOSSES;
  return bosses[Math.floor(Math.random() * bosses.length)];
};

export const getRandomHero = (): string => {
  const heroes = IMAGES.HEROES;
  return heroes[Math.floor(Math.random() * heroes.length)];
};

// Character rarity mapping based on Discord bot hunters.json
export const CHARACTER_RARITY = {
  // SSR (Legendary) - Highest tier
  LEGENDARY: [
    IMAGES.CHARACTERS.THOMAS_ANDRE,
    IMAGES.CHARACTERS.CHA_HAE_IN,
    IMAGES.CHARACTERS.SHIMIZU_AKARI,
    IMAGES.CHARACTERS.ISLA_WRIGHT,
    IMAGES.CHARACTERS.BAEK_YOONHO,
    IMAGES.CHARACTERS.CHOI_JONG_IN,
  ],
  // SR (Epic) - High tier
  EPIC: [
    IMAGES.CHARACTERS.GO_GUNHEE,
    IMAGES.CHARACTERS.WOO_JINCHUL,
    IMAGES.CHARACTERS.GOTO_RYUJI,
    IMAGES.CHARACTERS.ESIL_RADIRU,
    IMAGES.CHARACTERS.MEILIN_FISHER,
    IMAGES.CHARACTERS.ALICIA_BLANCHE,
  ],
  // R (Rare) - Mid tier
  RARE: [
    IMAGES.CHARACTERS.HAN_SE_MI,
    IMAGES.CHARACTERS.CHARLOTTE,
    IMAGES.CHARACTERS.AMAMIYA_MIREI,
    IMAGES.CHARACTERS.ANNA_RUIZ,
    IMAGES.CHARACTERS.EMMA_LAURENT,
    IMAGES.CHARACTERS.SEO_JIWOO,
  ],
  // N (Common) - Low tier
  COMMON: [
    IMAGES.CHARACTERS.GINA,
    IMAGES.CHARACTERS.HARPER,
    IMAGES.CHARACTERS.CARL,
    IMAGES.CHARACTERS.MIN_BYUNG_GU,
    IMAGES.CHARACTERS.KIM_SANGSHIK,
    IMAGES.CHARACTERS.JO_KYUHWAN,
  ],
};
