--
-- PostgreSQL database dump
--

\restrict wexnqzlbSe1EJvLqZxADbKhtQa6u8mRoRRdKPQ0gQJY7AyUKxJpC6god9tncfwq

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: financials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financials (
    id integer NOT NULL,
    property_id integer,
    revenue bigint NOT NULL,
    net_income bigint NOT NULL,
    expenses bigint NOT NULL
);


ALTER TABLE public.financials OWNER TO postgres;

--
-- Name: financials_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.financials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.financials_id_seq OWNER TO postgres;

--
-- Name: financials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.financials_id_seq OWNED BY public.financials.id;


--
-- Name: properties; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.properties (
    property_id integer NOT NULL,
    address character varying(255) NOT NULL,
    metro_area character varying(100) NOT NULL,
    sq_footage integer NOT NULL,
    property_type character varying(50) NOT NULL
);


ALTER TABLE public.properties OWNER TO postgres;

--
-- Name: properties_property_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.properties_property_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.properties_property_id_seq OWNER TO postgres;

--
-- Name: properties_property_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.properties_property_id_seq OWNED BY public.properties.property_id;


--
-- Name: financials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financials ALTER COLUMN id SET DEFAULT nextval('public.financials_id_seq'::regclass);


--
-- Name: properties property_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.properties ALTER COLUMN property_id SET DEFAULT nextval('public.properties_property_id_seq'::regclass);


--
-- Data for Name: financials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.financials (id, property_id, revenue, net_income, expenses) FROM stdin;
1	1	14200000	4100000	8900000
2	2	3800000	920000	2100000
3	3	11500000	3400000	7200000
4	4	2900000	680000	1700000
5	5	6200000	1800000	3900000
6	6	5100000	1400000	3100000
7	7	2600000	590000	1500000
8	8	8900000	2600000	5500000
9	9	1700000	410000	980000
10	10	4800000	1300000	2900000
11	11	6100000	1750000	3800000
12	12	2200000	520000	1300000
13	13	4100000	1100000	2500000
14	14	7200000	2100000	4400000
15	15	3900000	1050000	2300000
16	16	2400000	550000	1400000
17	17	9800000	2900000	6100000
18	18	6400000	1850000	3900000
19	19	1900000	450000	1100000
20	20	8100000	2350000	5000000
21	21	5600000	1600000	3400000
22	22	3500000	820000	2100000
\.


--
-- Data for Name: properties; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.properties (property_id, address, metro_area, sq_footage, property_type) FROM stdin;
1	233 S Wacker Dr	Chicago	1850000	Office
2	350 N Orleans St	Chicago	420000	Industrial
3	1 Infinite Loop	San Francisco	980000	Office
4	2000 W Fulton St	Chicago	310000	Industrial
5	555 Market St	San Francisco	670000	Retail
6	100 Main St	Dallas	540000	Mixed-Use
7	400 Commerce St	Dallas	280000	Industrial
8	1200 Brickell Ave	Miami	760000	Office
9	88 NW 7th St	Miami	190000	Retail
10	5000 Forbes Ave	Pittsburgh	430000	Office
11	300 W Adams St	Chicago	510000	Office
12	1401 S Michigan Ave	Chicago	240000	Retail
13	900 Market St	San Francisco	380000	Retail
14	2500 Ross Ave	Dallas	620000	Office
15	3100 McKinnon St	Dallas	350000	Mixed-Use
16	200 SE 1st St	Miami	290000	Industrial
17	777 Brickell Ave	Miami	840000	Office
18	1 PPG Place	Pittsburgh	570000	Office
19	4400 Fifth Ave	Pittsburgh	210000	Retail
20	600 W Chicago Ave	Chicago	730000	Mixed-Use
21	150 California St	San Francisco	490000	Office
22	3000 Stemmons Fwy	Dallas	460000	Industrial
\.


--
-- Name: financials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.financials_id_seq', 22, true);


--
-- Name: properties_property_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.properties_property_id_seq', 1, false);


--
-- Name: financials financials_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financials
    ADD CONSTRAINT financials_pkey PRIMARY KEY (id);


--
-- Name: properties properties_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_pkey PRIMARY KEY (property_id);


--
-- Name: financials financials_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financials
    ADD CONSTRAINT financials_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- PostgreSQL database dump complete
--

\unrestrict wexnqzlbSe1EJvLqZxADbKhtQa6u8mRoRRdKPQ0gQJY7AyUKxJpC6god9tncfwq

