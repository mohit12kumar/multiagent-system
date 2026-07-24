-- Seed Canonical Entities for Disambiguation testing

INSERT INTO canonical_entities (id, name, type, description, wikidata_id) VALUES
('c1', 'Google', 'ORGANIZATION', 'Google LLC is an American multinational technology company focusing on search engine technology, online advertising, cloud computing, computer software, quantum computing, e-commerce, artificial intelligence, and consumer electronics.', 'Q95'),
('c2', 'Microsoft', 'ORGANIZATION', 'Microsoft Corporation is an American multinational technology corporation headquartered in Redmond, Washington.', 'Q2283'),
('c3', 'Apple Inc.', 'ORGANIZATION', 'Apple Inc. is an American multinational technology company headquartered in Cupertino, California.', 'Q312'),
('c4', 'New York City', 'LOCATION', 'New York, often called New York City, is the most populous city in the United States.', 'Q60'),
('c5', 'London', 'LOCATION', 'London is the capital and largest city of England and the United Kingdom.', 'Q84'),
('c6', 'Barack Obama', 'PERSON', 'Barack Hussein Obama II is an American politician who served as the 44th president of the United States from 2009 to 2017.', 'Q76'),
('c7', 'Elon Musk', 'PERSON', 'Elon Reeve Musk is a businessman and investor. He is the founder, chairman, CEO, and CTO of SpaceX; angel investor, CEO, product architect, and former chairman of Tesla, Inc.', 'Q9076'),
('c8', 'United Nations', 'ORGANIZATION', 'The United Nations is an international organization founded in 1945. It is currently made up of 193 Member States.', 'Q1065');
