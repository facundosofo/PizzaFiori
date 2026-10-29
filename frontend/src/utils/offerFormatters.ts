export const getCategoryOfferDescriptionParts = (
  quantity: number,
  categoryName: string,
): { quantityLabel: string; description: string } => {
  let quantityLabel: string;
  let quantityUnit = "";
  if ([0.125, 0.25, 0.5].some((portion) => Math.abs(quantity - portion) < 1e-9)) {
    quantityLabel = "1";
    quantityUnit = " porción";
  } else if (Math.abs(quantity - 6) < 1e-9) {
    quantityLabel = "1/2";
    quantityUnit = " docena";
  } else if (quantity >= 12 && quantity % 12 === 0) {
    const dozens = quantity / 12;
    quantityLabel = new Intl.NumberFormat("es-AR", {
      maximumFractionDigits: 6,
    }).format(dozens);
    quantityUnit = ` docena${dozens === 1 ? "" : "s"}`;
  } else {
    quantityLabel = new Intl.NumberFormat("es-AR", {
      maximumFractionDigits: 6,
    }).format(quantity);
  }

  return {
    quantityLabel,
    description: `${quantityUnit} de ${categoryName.toLocaleLowerCase("es-AR")} a elección`,
  };
};

export const formatCategoryOfferDescription = (
  quantity: number,
  categoryName: string,
): string => {
  const parts = getCategoryOfferDescriptionParts(quantity, categoryName);
  return `${parts.quantityLabel}${parts.description}`;
};
