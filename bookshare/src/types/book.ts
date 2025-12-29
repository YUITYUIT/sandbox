export type Book = {
  id: string;
  imageUrl: string;
  title: string;
  author: string;
  publisher: string;
  publishedYear: number;
  reviews: Review[];
};

export type Review = {
  reader: string;
  rating: 1 | 2 | 3 | 4 | 5; // 1: 最低評価, 5: 最高評価
  comment: string;
};
