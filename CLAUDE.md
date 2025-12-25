# CLAUDE.md - AI Assistant Guide for nitro-ideas

## Repository Overview

**nitro-ideas** is a documentation repository containing personalized health, fitness, and lifestyle plans. The content is written in Portuguese (Brazilian Portuguese) and focuses on body composition improvement strategies.

## Repository Structure

```
nitro-ideas/
├── CLAUDE.md                        # AI assistant guidelines (this file)
└── plano-composicao-corporal.md     # Personalized body composition plans
```

### Current Content

- **plano-composicao-corporal.md**: Contains detailed body composition improvement plans for individuals, including:
  - Personal health metrics analysis
  - Nutrition plans with macronutrient breakdowns
  - Training schedules and exercise recommendations
  - Supplementation suggestions
  - Progress monitoring guidelines

## Content Conventions

### Language

- All content should be written in **Brazilian Portuguese**
- Use clear, accessible language appropriate for health and fitness guidance
- Technical terms should be explained when first introduced

### Markdown Formatting

- Use hierarchical headers (H1 for main title, H2 for sections, H3 for subsections)
- Use tables for structured data (metrics, meal plans, training schedules)
- Use horizontal rules (`---`) to separate major sections
- Use bold for emphasis on key terms and values
- Use bullet points for lists of items, foods, or recommendations

### Document Structure Pattern

When creating new plans or documents, follow this structure:

1. **Title** (H1)
2. **Summary/Analysis** (H2) - Overview of current state and goals
3. **Personalized Plans** (H2) - Detailed recommendations per individual
   - Objectives (H3)
   - Nutrition (H3)
   - Training (H3)
   - Supplementation (H3)
4. **Timeline/Goals** (H2) - Phased approach with measurable targets
5. **Monitoring** (H2) - How to track progress
6. **Important Notes** (H2) - Disclaimers and additional guidance

## Development Workflow

### Adding New Content

1. Create new `.md` files for distinct topics or individuals
2. Follow the established formatting conventions
3. Ensure all numeric data is presented in tables for readability
4. Include professional disclaimers when providing health-related advice

### Editing Existing Content

1. Preserve the existing document structure
2. Update tables with new metrics when available
3. Add dated sections for progress updates if needed
4. Maintain consistency in units (kg, cm, kcal, g)

## Domain-Specific Guidelines

### Health and Fitness Content

- Always include disclaimer about consulting professionals
- Use evidence-based recommendations
- Present realistic, sustainable approaches
- Include both short-term and long-term goals
- Provide measurable indicators of success

### Metric Standards

| Type | Unit | Format Example |
|------|------|----------------|
| Weight | kg | 53.7 kg |
| Height | cm | 159 cm |
| Body fat | kg and % | 18.5 kg (34.5%) |
| Calories | kcal | 1400 kcal |
| Protein/Carbs/Fat | g/day | 85-107g/dia |
| Protein per kg | g/kg | 1.6-2.0 g/kg |

### Training Terminology

- **HIIT**: High-Intensity Interval Training
- **LISS**: Low-Intensity Steady State
- **Séries**: Sets
- **Repetições**: Repetitions

## Git Workflow

- Use descriptive commit messages in Portuguese
- Example: "Adiciona plano personalizado de composição corporal"
- Keep commits focused on single logical changes

## Notes for AI Assistants

1. **Respect privacy**: When updating plans, maintain the existing structure without revealing or exposing additional personal information
2. **Evidence-based**: Recommendations should align with established nutrition and exercise science
3. **Consistency**: Match the existing tone and formatting of documents
4. **Professional disclaimer**: Always remind users to consult healthcare professionals
5. **Units**: Use metric system (kg, cm, etc.) consistently
