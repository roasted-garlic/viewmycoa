--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8
-- Dumped by pg_dump version 16.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO neondb_owner;

--
-- Name: batch_history; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.batch_history (
    id integer NOT NULL,
    product_id integer NOT NULL,
    batch_number character varying(8) NOT NULL,
    attributes text,
    coa_pdf character varying(500),
    created_at timestamp without time zone
);


ALTER TABLE public.batch_history OWNER TO neondb_owner;

--
-- Name: batch_history_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.batch_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.batch_history_id_seq OWNER TO neondb_owner;

--
-- Name: batch_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.batch_history_id_seq OWNED BY public.batch_history.id;


--
-- Name: category; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.category (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp without time zone,
    square_category_id character varying(255)
);


ALTER TABLE public.category OWNER TO neondb_owner;

--
-- Name: category_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.category_id_seq OWNER TO neondb_owner;

--
-- Name: category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.category_id_seq OWNED BY public.category.id;


--
-- Name: generated_pdf; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.generated_pdf (
    id integer NOT NULL,
    product_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    created_at timestamp without time zone,
    pdf_url character varying(500),
    batch_history_id integer
);


ALTER TABLE public.generated_pdf OWNER TO neondb_owner;

--
-- Name: generated_pdf_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.generated_pdf_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.generated_pdf_id_seq OWNER TO neondb_owner;

--
-- Name: generated_pdf_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.generated_pdf_id_seq OWNED BY public.generated_pdf.id;


--
-- Name: product; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.product (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    batch_number character varying(8),
    sku character varying(8),
    barcode character varying(12),
    attributes text,
    cost double precision,
    price double precision,
    product_image character varying(500),
    label_image character varying(500),
    coa_pdf character varying(500),
    template_id integer,
    craftmypdf_template_id character varying(255),
    label_qty integer NOT NULL,
    created_at timestamp without time zone,
    square_catalog_id character varying(255),
    square_image_id character varying(255)
);


ALTER TABLE public.product OWNER TO neondb_owner;

--
-- Name: product_categories; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.product_categories (
    product_id integer,
    category_id integer
);


ALTER TABLE public.product_categories OWNER TO neondb_owner;

--
-- Name: product_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_id_seq OWNER TO neondb_owner;

--
-- Name: product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.product_id_seq OWNED BY public.product.id;


--
-- Name: product_template; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.product_template (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    attributes text,
    created_at timestamp without time zone
);


ALTER TABLE public.product_template OWNER TO neondb_owner;

--
-- Name: product_template_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.product_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_template_id_seq OWNER TO neondb_owner;

--
-- Name: product_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.product_template_id_seq OWNED BY public.product_template.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.settings (
    id integer NOT NULL,
    show_square_id_controls boolean NOT NULL,
    show_square_image_id_controls boolean NOT NULL,
    square_environment character varying(20) NOT NULL,
    square_sandbox_access_token character varying(255),
    square_sandbox_location_id character varying(255),
    square_production_access_token character varying(255),
    square_production_location_id character varying(255),
    craftmypdf_api_key character varying(255)
);


ALTER TABLE public.settings OWNER TO neondb_owner;

--
-- Name: settings_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.settings_id_seq OWNER TO neondb_owner;

--
-- Name: settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.settings_id_seq OWNED BY public.settings.id;


--
-- Name: batch_history id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.batch_history ALTER COLUMN id SET DEFAULT nextval('public.batch_history_id_seq'::regclass);


--
-- Name: category id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.category ALTER COLUMN id SET DEFAULT nextval('public.category_id_seq'::regclass);


--
-- Name: generated_pdf id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.generated_pdf ALTER COLUMN id SET DEFAULT nextval('public.generated_pdf_id_seq'::regclass);


--
-- Name: product id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product ALTER COLUMN id SET DEFAULT nextval('public.product_id_seq'::regclass);


--
-- Name: product_template id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product_template ALTER COLUMN id SET DEFAULT nextval('public.product_template_id_seq'::regclass);


--
-- Name: settings id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.settings ALTER COLUMN id SET DEFAULT nextval('public.settings_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.alembic_version (version_num) FROM stdin;
\.


--
-- Data for Name: batch_history; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.batch_history (id, product_id, batch_number, attributes, coa_pdf, created_at) FROM stdin;
\.


--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.category (id, name, description, created_at, square_category_id) FROM stdin;
6	Disposables		2024-12-23 19:23:41.355937	\N
5	Gummies		2024-12-20 02:58:36.630212	\N
3	Flower		2024-12-19 20:11:29.024011	\N
4	Pre-Rolls		2024-12-19 23:28:49.835281	\N
7	Edibles		2025-02-22 22:22:10.643225	\N
\.


--
-- Data for Name: generated_pdf; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.generated_pdf (id, product_id, filename, created_at, pdf_url, batch_history_id) FROM stdin;
62	12	history_label_4KFKAXTY_20241218_233608.pdf	2024-12-18 23:35:54.089386	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/history_label_4KFKAXTY_20241218_233608.pdf	\N
63	12	label_GPZVFKQ8_20241218_235421.pdf	2024-12-18 23:54:23.014644	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/GPZVFKQ8/label_GPZVFKQ8_20241218_235421.pdf	\N
64	12	BJF6FQL3/history_label_BJF6FQL3_20241218_235838.pdf	2024-12-18 23:58:27.284223	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/BJF6FQL3/history_label_BJF6FQL3_20241218_235838.pdf	\N
65	12	JICKUSJ8/history_label_JICKUSJ8_20241219_000836.pdf	2024-12-19 00:08:08.749554	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/JICKUSJ8/history_label_JICKUSJ8_20241219_000836.pdf	\N
66	12	4F5AE0CK/history_label_4F5AE0CK_20241219_001349.pdf	2024-12-19 00:13:42.171462	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/4F5AE0CK/history_label_4F5AE0CK_20241219_001349.pdf	\N
67	12	NT25SRAB/history_label_NT25SRAB_20241219_002336.pdf	2024-12-19 00:23:18.377386	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/NT25SRAB/history_label_NT25SRAB_20241219_002336.pdf	\N
68	12	95C8DKXT/history_label_95C8DKXT_20241219_002550.pdf	2024-12-19 00:25:11.910656	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/95C8DKXT/history_label_95C8DKXT_20241219_002550.pdf	\N
69	12	8DUU10S8/history_label_8DUU10S8_20241219_002824.pdf	2024-12-19 00:28:13.507914	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/8DUU10S8/history_label_8DUU10S8_20241219_002824.pdf	\N
70	12	2RIVHU8P/history_label_2RIVHU8P_20241219_003725.pdf	2024-12-19 00:31:30.942641	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/2RIVHU8P/history_label_2RIVHU8P_20241219_003725.pdf	\N
71	12	93AADVHU/history_label_93AADVHU_20241219_003841.pdf	2024-12-19 00:38:21.511422	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/93AADVHU/history_label_93AADVHU_20241219_003841.pdf	\N
72	12	9NQG7ZEO/history_label_9NQG7ZEO_20241219_004327.pdf	2024-12-19 00:42:49.259076	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/9NQG7ZEO/history_label_9NQG7ZEO_20241219_004327.pdf	\N
73	12	EGG64U8G/history_label_EGG64U8G_20241219_010415.pdf	2024-12-19 00:44:31.844047	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/EGG64U8G/history_label_EGG64U8G_20241219_010415.pdf	\N
77	12	label_3KTRWJ1A_20241219_224128.pdf	2024-12-19 22:41:35.381574	http://33bc90e3-4b23-41c5-b18d-3ed153949c16-00-3i50tf8upz4wc.janeway.replit.dev/static/pdfs/3KTRWJ1A/label_3KTRWJ1A_20241219_224128.pdf	\N
136	12	label_EK0CEVP1_20241229_010917.pdf	2024-12-29 01:09:19.339341	http://viewmycoa.replit.app/static/pdfs/EK0CEVP1/label_EK0CEVP1_20241229_010917.pdf	\N
137	11	label_KH9QQE5C_20241229_011004.pdf	2024-12-29 01:10:06.280906	http://viewmycoa.replit.app/static/pdfs/KH9QQE5C/label_KH9QQE5C_20241229_011004.pdf	\N
138	10	label_3KTRWJ1A_20241229_011023.pdf	2024-12-29 01:10:25.48279	http://viewmycoa.replit.app/static/pdfs/3KTRWJ1A/label_3KTRWJ1A_20241229_011023.pdf	\N
157	63	label_W1NRXRAZ_20250117_181019.pdf	2025-01-17 18:10:21.470783	http://viewmycoa.replit.app/static/pdfs/W1NRXRAZ/label_W1NRXRAZ_20250117_181019.pdf	\N
158	58	label_J3N7F8MO_20250117_181208.pdf	2025-01-17 18:12:10.345724	http://viewmycoa.replit.app/static/pdfs/J3N7F8MO/label_J3N7F8MO_20250117_181208.pdf	\N
160	56	label_Z1DOKMQI_20250117_181337.pdf	2025-01-17 18:13:39.245861	http://viewmycoa.replit.app/static/pdfs/Z1DOKMQI/label_Z1DOKMQI_20250117_181337.pdf	\N
162	57	label_G1UQTSV0_20250117_181446.pdf	2025-01-17 18:14:47.835261	http://viewmycoa.replit.app/static/pdfs/G1UQTSV0/label_G1UQTSV0_20250117_181446.pdf	\N
164	62	label_P8SZ2FLG_20250117_181934.pdf	2025-01-17 18:19:39.798812	http://viewmycoa.replit.app/static/pdfs/P8SZ2FLG/label_P8SZ2FLG_20250117_181934.pdf	\N
165	64	label_2VHZZY4V_20250117_182439.pdf	2025-01-17 18:24:41.676569	http://viewmycoa.replit.app/static/pdfs/2VHZZY4V/label_2VHZZY4V_20250117_182439.pdf	\N
167	57	label_G1UQTSV0_20250127_042025.pdf	2025-01-27 04:20:27.088743	http://viewmycoa.replit.app/static/pdfs/G1UQTSV0/label_G1UQTSV0_20250127_042025.pdf	\N
168	66	label_0DW369ZT_20250216_213201.pdf	2025-02-16 21:32:03.239997	http://viewmycoa.replit.app/static/pdfs/0DW369ZT/label_0DW369ZT_20250216_213201.pdf	\N
169	67	label_BG88RX5D_20250216_213333.pdf	2025-02-16 21:33:34.802119	http://viewmycoa.replit.app/static/pdfs/BG88RX5D/label_BG88RX5D_20250216_213333.pdf	\N
170	68	label_WICGKW71_20250216_213427.pdf	2025-02-16 21:34:28.657625	http://viewmycoa.replit.app/static/pdfs/WICGKW71/label_WICGKW71_20250216_213427.pdf	\N
171	69	label_3FHF9PO1_20250222_220131.pdf	2025-02-22 22:01:32.585878	http://viewmycoa.com/static/pdfs/3FHF9PO1/label_3FHF9PO1_20250222_220131.pdf	\N
172	65	label_LDH4DP31_20250222_220249.pdf	2025-02-22 22:02:50.729291	http://viewmycoa.com/static/pdfs/LDH4DP31/label_LDH4DP31_20250222_220249.pdf	\N
173	61	label_6BWBAXNA_20250222_220338.pdf	2025-02-22 22:03:39.412426	http://viewmycoa.com/static/pdfs/6BWBAXNA/label_6BWBAXNA_20250222_220338.pdf	\N
174	60	label_B14MEE98_20250222_220423.pdf	2025-02-22 22:04:24.605637	http://viewmycoa.com/static/pdfs/B14MEE98/label_B14MEE98_20250222_220423.pdf	\N
175	59	label_NCU08Y04_20250222_220517.pdf	2025-02-22 22:05:18.368499	http://viewmycoa.com/static/pdfs/NCU08Y04/label_NCU08Y04_20250222_220517.pdf	\N
176	71	label_FLHL91NF_20250222_220739.pdf	2025-02-22 22:07:40.925257	http://viewmycoa.com/static/pdfs/FLHL91NF/label_FLHL91NF_20250222_220739.pdf	\N
177	70	label_KGDRTRZX_20250222_220811.pdf	2025-02-22 22:08:12.601049	http://viewmycoa.com/static/pdfs/KGDRTRZX/label_KGDRTRZX_20250222_220811.pdf	\N
179	73	label_HO6TMMOO_20250222_221334.pdf	2025-02-22 22:13:36.159512	http://viewmycoa.com/static/pdfs/HO6TMMOO/label_HO6TMMOO_20250222_221334.pdf	\N
180	72	label_DT831O64_20250222_221350.pdf	2025-02-22 22:13:51.704108	http://viewmycoa.com/static/pdfs/DT831O64/label_DT831O64_20250222_221350.pdf	\N
181	74	label_P7H8G6FG_20250222_221442.pdf	2025-02-22 22:14:43.952692	http://viewmycoa.com/static/pdfs/P7H8G6FG/label_P7H8G6FG_20250222_221442.pdf	\N
\.


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.product (id, title, batch_number, sku, barcode, attributes, cost, price, product_image, label_image, coa_pdf, template_id, craftmypdf_template_id, label_qty, created_at, square_catalog_id, square_image_id) FROM stdin;
57	Gorilla Glue #4 - Live Resin - 1g Disposable	G1UQTSV0	JE363378	304660650637	{"cannabinoid": "THCa", "terpene_profile": "Gorilla Glue #4 - Hybrid", "total_gram_weight": "1g", "total_mg": "900mg"}	9.75	52	uploads/57/product_image_57.png	uploads/57/label_image_57.png	\N	\N	83577b23a23d34ac	4	2025-01-04 18:09:04.200629	\N	\N
10	Peach OG - THCa Flower	3KTRWJ1A	NA809740	147354423940	{"cannabinoid": "THCa", "flower_strain_name": "Peach OG", "gram_weight": "3.5g", "strain_type": "Indica", "total_precent": "31.4%"}	7.4	40	uploads/10/product_image_10.png	uploads/10/label_image_10.png	\N	\N	83577b23a23d34ac	4	2024-12-20 15:39:02.347945	\N	\N
11	Zerbert - THCa Flower	KH9QQE5C	YK431087	755749168183	{"cannabinoid": "THCa", "flower_strain_name": "Zerbert", "gram_weight": "3.5g", "strain_type": "Hybrid", "total_precent": "30%"}	7.4	40	uploads/11/product_image_11.png	uploads/11/label_image_11.png	\N	\N	83577b23a23d34ac	4	2024-12-20 15:40:08.025412	\N	\N
12	GovernMint Oasis - THCa Flower	EK0CEVP1	QZ865202	063553301662	{"cannabinoid": "THCa", "flower_strain_name": "GovernMint Oasis", "gram_weight": "3.5g", "strain_type": "50/50 Hybrid", "total_precent": "30%"}	7.4	40	uploads/12/product_image_12.png	uploads/12/label_image_12.png	\N	\N	83577b23a23d34ac	4	2024-12-20 15:41:12.044788	\N	\N
63	Trainwreck - Live Resin - 1g Disposable	W1NRXRAZ	TK813660	316735782893	{"cannabinoid": "THCa", "terpene_profile": "Trainwreck - Sativa", "total_gram_weight": "1g", "total_mg": "900mg"}	9.75	52	uploads/63/product_image_63.png	uploads/63/label_image_63.png	\N	\N	83577b23a23d34ac	4	2025-01-17 18:08:58.954869	\N	\N
69	Jack Herer - 2g Diamond Blunts	3FHF9PO1	TJ815922	065918150586	{"cannabinoid": "THCa", "strain_name": "Jack Herer - Diamond", "strain_type": "Sativa", "total_cannabinoids": "Approx. 42%", "weight": "2g"}	3.75	18	uploads/69/product_image_69.png	uploads/69/label_image_69.png	\N	\N	28477b23a29fd66e	8	2025-02-22 22:00:32.487085	\N	\N
65	Trainwreck - 2g Diamond Blunts	LDH4DP31	BI239830	266390244035	{"cannabinoid": "THCa", "strain_name": "Trainwreck  - Diamond", "strain_type": "Sativa", "total_cannabinoids": "Approx. 39%", "weight": "2g"}	3.75	18	uploads/65/product_image_65.png	uploads/65/label_image_65.png	\N	\N	28477b23a29fd66e	8	2025-01-17 18:16:55.169343	\N	\N
62	Blue Dreams - Live Resin - 1g Disposable	P8SZ2FLG	KC389136	733188371560	{"cannabinoid": "THCa", "terpene_profile": "Blue Dreams - Hybrid", "total_gram_weight": "1g", "total_mg": "900mg"}	9.75	52	uploads/62/product_image_62.png	uploads/62/label_image_62.png	\N	\N	83577b23a23d34ac	4	2025-01-17 18:07:46.142098	\N	\N
64	Wedding Cake - Live Resin - 1g Disposable	2VHZZY4V	PU369054	884689742736	{"cannabinoid": "THCa", "terpene_profile": "Wedding Cake - Hybrid", "total_gram_weight": "1g", "total_mg": "900mg"}	9.75	52	uploads/64/product_image_64.png	uploads/64/label_image_64.png	\N	\N	83577b23a23d34ac	4	2025-01-17 18:10:42.385881	\N	\N
58	Jack Herer - Live Resin - 1g Disposable	J3N7F8MO	FN551993	541064684365	{"cannabinoid": "THCa", "terpene_profile": "Jack Herer - Sativa", "total_gram_weight": "1g", "total_mg": "900mg"}	9.75	52	uploads/58/product_image_58.png	uploads/58/label_image_58.png	\N	\N	83577b23a23d34ac	4	2025-01-04 18:10:53.010541	\N	\N
66	Grandaddy Purple - CBD Pre-Roll	0DW369ZT	BU948087	873734777733	{"cannabinoid": "CBD", "strain_name": "Grandaddy Purple", "strain_type": "Indica", "total_cannabinoids": "Approx. 18%", "weight": "1g"}	1	8	uploads/66/product_image_66.png	uploads/66/label_image_66.png	\N	\N	28477b23a29fd66e	8	2025-02-16 21:23:22.497243	\N	\N
56	Granddaddy Purple - Live Resin - 1g Disposable	Z1DOKMQI	SQ722011	389146487882	{"cannabinoid": "THCa", "terpene_profile": "Granddaddy Purple - Indica", "total_gram_weight": "1g", "total_mg": "900mg"}	9.75	52	uploads/56/product_image_56.png	uploads/56/label_image_56.png	\N	\N	83577b23a23d34ac	4	2025-01-04 18:06:19.842848	\N	\N
61	Frosted Grape - 2g Diamond Blunts	6BWBAXNA	SU049821	822214040191	{"cannabinoid": "THCa", "strain_name": "Frosted Grape - Diamond", "strain_type": "Indica", "total_cannabinoids": "Approx. 39%", "weight": "2g"}	3.75	18	uploads/61/product_image_61.png	uploads/61/label_image_61.png	\N	\N	28477b23a29fd66e	8	2025-01-04 18:44:48.756162	\N	\N
68	Bomb Pop - CBD Pre-Roll	WICGKW71	XN472370	551526647832	{"cannabinoid": "CBD", "strain_name": "Bomb Pop", "strain_type": "Hybrid", "total_cannabinoids": "Approx. 18%", "weight": "1g"}	1	8	uploads/68/product_image_68.png	uploads/68/label_image_68.png	\N	\N	28477b23a29fd66e	8	2025-02-16 21:33:57.177685	\N	\N
60	Gorilla Glue #4 - 2g Diamond Blunts	B14MEE98	TD826926	740516318191	{"cannabinoid": "THCa", "strain_name": "Gorilla Glue #4 - Diamond", "strain_type": "Hybrid", "total_cannabinoids": "Approx. 33%", "weight": "2g"}	3.75	18	uploads/60/product_image_60.png	uploads/60/label_image_60.png	\N	\N	28477b23a29fd66e	8	2025-01-04 18:41:56.959051	\N	\N
59	Strawberry Cough - 2g Diamond Blunts	NCU08Y04	ST487648	069254068138	{"cannabinoid": "THCa", "strain_name": "Strawberry Cough - Diamond", "strain_type": "Sativa", "total_cannabinoids": "Approx. 39%", "weight": "2g"}	3.75	18	uploads/59/product_image_59.png	uploads/59/label_image_59.png	\N	\N	28477b23a29fd66e	8	2025-01-04 18:37:26.833563	\N	\N
70	Runtz - 2g Diamond Blunts	KGDRTRZX	TH604663	192677340328	{"cannabinoid": "THCa", "strain_name": "Runtz - Diamond", "strain_type": "Hybrid", "total_cannabinoids": "Approx. 42%", "weight": "2g"}	3.75	18	uploads/70/product_image_70.png	uploads/70/label_image_70.png	\N	\N	28477b23a29fd66e	8	2025-02-22 22:06:39.62659	\N	\N
67	Sour Diesel - CBD Pre-Roll	BG88RX5D	SP907079	220662320182	{"cannabinoid": "CBD", "strain_name": "Sour Diesel", "strain_type": "Sativa", "total_cannabinoids": "Approx. 18%", "weight": "1g"}	1	8	uploads/67/product_image_67.png	uploads/67/label_image_67.png	\N	\N	28477b23a29fd66e	8	2025-02-16 21:33:01.490169	\N	\N
71	Northern Lights - 2g Diamond Blunts	FLHL91NF	BW559648	425406467769	{"cannabinoid": "THCa", "strain_name": "Northern Lights - Diamond", "strain_type": "Hybrid", "total_cannabinoids": "Approx. 42%", "weight": "2g"}	3.75	18	uploads/71/product_image_71.png	uploads/71/label_image_71.png	\N	\N	28477b23a29fd66e	8	2025-02-22 22:07:14.301944	\N	\N
72	LemonCherry Gelato - THCa Pre-Rolls	DT831O64	RH603094	213527190477	{"cannabinoid": "THCa", "strain_name": "LemonCherry Gelato", "strain_type": "Sativa", "total_cannabinoids": "Approx. 28%", "weight": "1g"}	3	14	uploads/72/product_image_72.png	uploads/72/label_image_72.png	\N	\N	28477b23a29fd66e	8	2025-02-22 22:09:03.636723	\N	\N
73	Skittlez Mints - THCa Pre-Rolls	HO6TMMOO	OA661971	155166001454	{"cannabinoid": "THCa", "strain_name": "Skittlez Mints", "strain_type": "Hybrid", "total_cannabinoids": "Approx. 25%", "weight": "1g"}	3	14	uploads/73/product_image_73.png	uploads/73/label_image_73.png	\N	\N	28477b23a29fd66e	8	2025-02-22 22:12:16.875563	\N	\N
74	Sherbet - THCa Pre-Rolls	P7H8G6FG	MQ670426	273394768931	{"cannabinoid": "THCa", "strain_name": "Sherbet", "strain_type": "Hybrid", "total_cannabinoids": "Approx. 27%", "weight": "1g"}	3	14	uploads/74/product_image_74.png	uploads/74/label_image_74.png	\N	\N	28477b23a29fd66e	8	2025-02-22 22:14:04.777709	\N	\N
\.


--
-- Data for Name: product_categories; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.product_categories (product_id, category_id) FROM stdin;
12	3
10	3
11	3
12	3
56	6
57	6
58	6
59	4
60	4
61	4
62	6
63	6
64	6
65	4
66	4
67	4
68	4
69	4
70	4
71	4
72	4
73	4
74	4
\.


--
-- Data for Name: product_template; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.product_template (id, name, attributes, created_at) FROM stdin;
3	Flower - Indica -3.5g	{"cannabinoid": "THCa", "flower_strain_name": "", "strain_type": "Indica", "gram_weight": "3.5g", "total_precent": ""}	2024-12-18 16:26:08.801187
8	Flower - Sativa -3.5g	{"cannabinoid": "THCa", "flower_strain_name": "", "strain_type": "Sativa", "gram_weight": "3.5g", "total_precent": ""}	2024-12-20 22:38:29.719911
9	Flower - Hybrid -3.5g	{"cannabinoid": "THCa", "flower_strain_name": "", "strain_type": "Hybrid", "gram_weight": "3.5g", "total_precent": ""}	2024-12-20 22:38:45.567893
10	Gummies - 10mg Delta 9	{"cannabinoid": "Delta 9", "mg_per_piece": "10mg", "flavor": "", "count": "20", "per_piece_g": "4.5g", "net_weight_g": "90g"}	2024-12-27 18:58:38.266583
11	Disposable - 1g THCa	{"cannabinoid": "THCa", "total_mg": "900mg", "terpene_profile": "", "total_gram_weight": "1g"}	2025-01-04 17:55:15.641917
12	Blunts - Indica - 2g	{"cannabinoid": "THCa", "strain_name": "", "strain_type": "Indica", "weight": "2g", "total_cannabinoids": ""}	2025-01-04 18:27:32.432309
13	Blunts - Sativa - 2g	{"cannabinoid": "THCa", "strain_name": "", "strain_type": "Sativa", "weight": "2g", "total_cannabinoids": ""}	2025-01-04 18:32:47.351468
14	Blunts - Hybrid - 2g	{"cannabinoid": "THCa", "strain_name": "", "strain_type": "Hybrid", "weight": "2g", "total_cannabinoids": ""}	2025-01-04 18:32:59.328421
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.settings (id, show_square_id_controls, show_square_image_id_controls, square_environment, square_sandbox_access_token, square_sandbox_location_id, square_production_access_token, square_production_location_id, craftmypdf_api_key) FROM stdin;
1	f	f	sandbox					5318MTU6MTM1ODpHakI2b2psNnl5NndvMDd
\.


--
-- Name: batch_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.batch_history_id_seq', 42, true);


--
-- Name: category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.category_id_seq', 7, true);


--
-- Name: generated_pdf_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.generated_pdf_id_seq', 181, true);


--
-- Name: product_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.product_id_seq', 74, true);


--
-- Name: product_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.product_template_id_seq', 14, true);


--
-- Name: settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.settings_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: batch_history batch_history_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.batch_history
    ADD CONSTRAINT batch_history_pkey PRIMARY KEY (id);


--
-- Name: category category_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_name_key UNIQUE (name);


--
-- Name: category category_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_pkey PRIMARY KEY (id);


--
-- Name: generated_pdf generated_pdf_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.generated_pdf
    ADD CONSTRAINT generated_pdf_pkey PRIMARY KEY (id);


--
-- Name: product product_barcode_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_barcode_key UNIQUE (barcode);


--
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_pkey PRIMARY KEY (id);


--
-- Name: product product_sku_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_sku_key UNIQUE (sku);


--
-- Name: product_template product_template_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product_template
    ADD CONSTRAINT product_template_pkey PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: batch_history batch_history_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.batch_history
    ADD CONSTRAINT batch_history_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(id) ON DELETE CASCADE;


--
-- Name: generated_pdf fk_generated_pdf_batch_history; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.generated_pdf
    ADD CONSTRAINT fk_generated_pdf_batch_history FOREIGN KEY (batch_history_id) REFERENCES public.batch_history(id) ON DELETE CASCADE;


--
-- Name: generated_pdf generated_pdf_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.generated_pdf
    ADD CONSTRAINT generated_pdf_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(id) ON DELETE CASCADE;


--
-- Name: product_categories product_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.category(id) ON DELETE CASCADE;


--
-- Name: product_categories product_categories_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(id) ON DELETE CASCADE;


--
-- Name: product product_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.product_template(id) ON DELETE SET NULL;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

