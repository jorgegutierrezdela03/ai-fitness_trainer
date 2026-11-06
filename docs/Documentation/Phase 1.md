# Phase 1: Definition, initial baseline and evaluations
 **Objetive**: To have a reproducible core system that generates training sessions based on the user's profile and request, without relying on external knowledge, and to have a protocol for evaluating the results.

## P1-01 — Define project scope and requirements

Define the scope, target users, functional requirements, and constraints of the AI Fitness Trainer baseline.

### P1-01.1 — Define Target Population and Project Scope
**Objective**: Define the target users, training objectives, and initial boundaries of the AI personal trainer.

#### Target Population
Adults aged 18 or older who perform or intend to perform exercise in a conventional gym, with different experience levels and general fitness goals.

#### Inclusion Criteria
- Generally healthy individuals without conditions requiring clinical exercise prescription.
- Beginners, intermediate and advanced recreational gym users.
- Users seeking personalized training for general fitness, strength, hypertrophy, muscular endurance, cardiovascular health, or body composition.

#### Exclusion Criteria
- Elite athletes requiring specialized training.
- Marathon, triathlon, or competitive endurance preparation.
- Competitive bodybuilding and specialized calisthenics.
- Clinical rehabilitation or medically supervised exercise.
- Nutritional planning and dietary interventions.

#### Training Context
The system will support conventional gym-based training using machines, dumbbells, barbells, free weights, cables, and cardiovascular equipment.

Supported objectives:
- Strength
- Hypertrophy
- Muscular endurance
- General fitness
- Fat loss through exercise
- Cardiovascular fitness
- Combined resistance and cardiovascular training

## P1-01.2 — Define User Profile Specifications
#
### Objective
i**ne the us**: 
### User Profile
#
#### Basic Information
- Age: Required.
- Sex: Optional.
- Height: Optional.
- Weight: Optional.

Height and weight will remain optional until their usefulness for different training objectives is evaluated.

#### Training Experience
Required. Three predefined levels:
- Beginner.
- Intermediate.
- Advanced.

#### Training Goals
Required. Select up to two primary objectives:
- Strength.
- Hypertrophy.
- Fat loss.
- Cardiovascular fitness.
- Muscular endurance.
- General fitness.

#### Training Availability
- Available training days per week: Required.
- Available session duration: Required.

#### Training Preferences and Restrictions
Optional questions covering:
- Exercises the user prefers to avoid. 
- Equipment or gym limitations.


The system will assume a conventional gym environment. With the possibily that a user has some preference or limitations in their place of training. 

#### Physical Limitations
Required Yes/No question:

**Do you have any physical limitations that may affect your training?**

If Yes:
- Select affected body areas (shoulder, elbow, wrist, back, hip, knee, ankle, or other).
- Provide an optional free-text description.

The system will use this information to identify and respect training restrictions without providing clinical or medical exercise prescription.

### Data Considerations
- P#rioritize structured inputs and predefined options.
- Use optional fields when information is not essential for initial plan generation.
- Minimize the collection of personal and health-related information.
- Initially use synthetic user profiles for experimental evaluation.
