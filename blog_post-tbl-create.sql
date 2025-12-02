-- public.blog_post definition

-- Drop table

-- DROP TABLE public.blog_post;

CREATE TABLE public.blog_post (
	root text NOT NULL,
	abbr_link text NOT NULL,
	title text NULL,
	base_url text NOT NULL,
	full_url text NOT NULL,
	create_date varchar(30) NULL,
	"content" text NULL,
	wayback_link1 text NULL,
	wayback_date1 varchar(30) NULL,
	wayback_link2 text NULL,
	wayback_date2 varchar(30) NULL,
	wayback_link3 text NULL,
	wayback_date3 varchar(30) NULL,
	wayback_link4 text NULL,
	wayback_date4 varchar(30) NULL,
	wayback_link5 text NULL,
	wayback_date5 varchar(30) NULL,
	CONSTRAINT pk_blog_post PRIMARY KEY (root, abbr_link)
);